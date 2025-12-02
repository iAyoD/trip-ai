import requests
import json

def test_plan_trip():
    url = "http://localhost:8000/api/trip/plan"
    payload = {
        "city": "Beijing",
        "start_date": "2023-10-01",
        "end_date": "2023-10-03",
        "days": 3,
        "preferences": "History and Culture",
        "budget": "Medium",
        "transportation": "Public Transport",
        "accommodation": "Economy Hotel"
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_plan_trip()
