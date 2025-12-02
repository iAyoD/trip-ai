from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import TripPlanRequest, TripPlan
from app.agents.trip_planner import TripPlannerAgent
from app.services.unsplash_service import UnsplashService
from app.config import get_settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Trip Planner API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
settings = get_settings()
trip_planner_agent = TripPlannerAgent()
unsplash_service = UnsplashService(settings.unsplash_access_key)

@app.post("/api/trip/plan", response_model=TripPlan)
async def create_trip_plan(request: TripPlanRequest) -> TripPlan:
    """
    创建旅行计划
    """
    logger.info(f"Received trip plan request for {request.city}")
    try:
        # 生成旅行计划
        trip_plan = trip_planner_agent.plan_trip(request)

        # 为每个景点获取图片
        for day in trip_plan.days:
            for attraction in day.attractions:
                if not attraction.image_url:
                    image_url = unsplash_service.get_photo_url(
                        f"{attraction.name} {trip_plan.city}"
                    )
                    attraction.image_url = image_url
        
        return trip_plan
    except Exception as e:
        logger.error(f"Error generating trip plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/poi/photo")
async def get_poi_photo(name: str):
    """
    获取景点图片
    """
    try:
        image_url = unsplash_service.get_photo_url(f"{name}")
        return {"success": True, "data": {"photo_url": image_url}}
    except Exception as e:
        logger.error(f"Error fetching photo for {name}: {e}")
        return {"success": False, "error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
