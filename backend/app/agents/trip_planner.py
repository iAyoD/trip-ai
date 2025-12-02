import json
from typing import List, Dict, Any
from hello_agents.core import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import MCPTool
from app.models.schemas import TripPlanRequest, TripPlan, DayPlan, WeatherInfo, Budget
from app.config import get_settings

# Prompts
ATTRACTION_AGENT_PROMPT = """你是景点搜索专家。

**工具调用格式:**
`[TOOL_CALL:amap_maps_text_search:keywords=景点,city=城市名]`

**示例:**
- `[TOOL_CALL:amap_maps_text_search:keywords=景点,city=北京]`
- `[TOOL_CALL:amap_maps_text_search:keywords=博物馆,city=上海]`

**重要:**
- 必须使用工具搜索,不要编造信息
- 根据用户偏好({preferences})搜索{city}的景点
"""

WEATHER_AGENT_PROMPT = """你是天气查询专家。

**工具调用格式:**
`[TOOL_CALL:amap_maps_weather:city=城市名]`

请查询{city}的天气信息。
"""

HOTEL_AGENT_PROMPT = """你是酒店推荐专家。

**工具调用格式:**
`[TOOL_CALL:amap_maps_text_search:keywords=酒店,city=城市名]`

请搜索{city}的{accommodation}酒店。
"""

PLANNER_AGENT_PROMPT = """你是行程规划专家。

**输出格式:**
严格按照以下JSON格式返回:
{
  "city": "城市名称",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "行程描述",
      "transportation": "交通方式",
      "accommodation": "住宿安排",
      "hotel": {
        "name": "酒店名称",
        "address": "地址",
        "estimated_cost": 0
      },
      "attractions": [
        {
          "name": "景点名称",
          "address": "地址",
          "location": {"longitude": 0, "latitude": 0},
          "visit_duration": 60,
          "description": "描述",
          "ticket_price": 0
        }
      ],
      "meals": [
        {
          "type": "lunch",
          "name": "餐厅名称",
          "estimated_cost": 0
        }
      ]
    }
  ],
  "weather_info": [
    {
      "date": "YYYY-MM-DD",
      "day_weather": "晴",
      "night_weather": "多云",
      "day_temp": 25,
      "night_temp": 18,
      "wind_direction": "东南",
      "wind_power": "3级"
    }
  ],
  "overall_suggestions": "总体建议",
  "budget": {
    "total_attractions": 0,
    "total_hotels": 0,
    "total_meals": 0,
    "total_transportation": 0,
    "total": 0
  }
}

**规划要求:**
1. weather_info必须包含每天的天气
2. 温度为纯数字(不带°C)
3. 每天安排2-3个景点
4. 考虑景点距离和游览时间
5. 包含早中晚三餐
6. 提供实用建议
7. 包含预算信息,根据景点门票、酒店价格、餐饮标准和交通方式估算
"""

class TripPlannerAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = HelloAgentsLLM()

        # 创建共享的MCP工具实例
        # Note: In a real scenario, we'd want to manage the lifecycle of this process better
        self.mcp_tool = MCPTool(
            name="amap_mcp",
            command="uvx", # Using uvx as per README recommendation for python environment
            args=["amap-mcp-server"], # Assuming the package is installed or available via uvx
            env={"AMAP_API_KEY": settings.amap_api_key},
            auto_expand=True
        )
        
        # Fallback if uvx doesn't work directly with the package name, 
        # we might need to install it first or use npx as in the original code.
        # But let's try to stick to python ecosystem if possible, or revert to npx if needed.
        # The README mentioned: "command='npx', args=['-y', '@sugarforever/amap-mcp-server']"
        # Let's stick to the README's npx command for reliability unless the user insists on python-only.
        # The user asked to use uv pip for dependencies, but this is an external tool.
        # Let's use npx for the MCP server as it's a node package.
        self.mcp_tool = MCPTool(
            name="amap_mcp",
            command="npx",
            args=["-y", "@sugarforever/amap-mcp-server"],
            env={"AMAP_API_KEY": settings.amap_api_key},
            auto_expand=True
        )

        self.attraction_agent = SimpleAgent(
            name="AttractionSearchAgent",
            llm=self.llm,
            system_prompt=ATTRACTION_AGENT_PROMPT
        )
        self.attraction_agent.add_tool(self.mcp_tool)

        self.weather_agent = SimpleAgent(
            name="WeatherQueryAgent",
            llm=self.llm,
            system_prompt=WEATHER_AGENT_PROMPT
        )
        self.weather_agent.add_tool(self.mcp_tool)

        self.hotel_agent = SimpleAgent(
            name="HotelAgent",
            llm=self.llm,
            system_prompt=HOTEL_AGENT_PROMPT
        )
        self.hotel_agent.add_tool(self.mcp_tool)

        self.planner_agent = SimpleAgent(
            name="PlannerAgent",
            llm=self.llm,
            system_prompt=PLANNER_AGENT_PROMPT
        )

    def _build_planner_query(
        self,
        request: TripPlanRequest,
        attraction_response: str,
        weather_response: str,
        hotel_response: str
    ) -> str:
        """构建规划Agent的查询"""
        return f"""
请根据以下信息生成{request.city}的{request.days}日旅行计划:

**用户需求:**
- 目的地: {request.city}
- 日期: {request.start_date} 至 {request.end_date}
- 天数: {request.days}天
- 偏好: {request.preferences}
- 预算: {request.budget}
- 交通方式: {request.transportation}
- 住宿类型: {request.accommodation}

**景点信息:**
{attraction_response}

**天气信息:**
{weather_response}

**酒店信息:**
{hotel_response}

请生成详细的旅行计划,包括每天的景点安排、餐饮推荐、住宿信息和预算明细。
"""

    def plan_trip(self, request: TripPlanRequest) -> TripPlan:
        # 步骤1: 景点搜索
        attraction_response = self.attraction_agent.run(
            f"请搜索{request.city}的{request.preferences}景点"
        )

        # 步骤2: 天气查询
        weather_response = self.weather_agent.run(
            f"请查询{request.city}的天气"
        )

        # 步骤3: 酒店推荐
        hotel_response = self.hotel_agent.run(
            f"请搜索{request.city}的{request.accommodation}酒店"
        )

        # 步骤4: 整合生成计划
        planner_query = self._build_planner_query(
            request, attraction_response, weather_response, hotel_response
        )
        planner_response = self.planner_agent.run(planner_query)

        # 步骤5: 解析JSON
        # Clean up response to ensure it's valid JSON
        json_str = planner_response
        if "```json" in json_str:
            start = json_str.find("```json") + 7
            end = json_str.find("```", start)
            json_str = json_str[start:end].strip()
        elif "```" in json_str:
            start = json_str.find("```") + 3
            end = json_str.find("```", start)
            json_str = json_str[start:end].strip()
            
        try:
            data = json.loads(json_str)
            return TripPlan(**data)
        except Exception as e:
            print(f"Error parsing plan: {e}")
            print(f"Raw response: {planner_response}")
            # Return a dummy plan or raise error
            raise ValueError("Failed to generate valid trip plan")
