import requests
import json

# Test the optimize-route endpoint
url = "http://localhost:5001/api/optimize-route"

data = {
    "userId": "user123",
    "route": {
        "origin": {
            "address": "123 Main St, New York",
            "coordinates": {"lat": 40.7128, "lng": -74.0060}
        },
        "destination": {
            "address": "456 Park Ave, New York",
            "coordinates": {"lat": 40.7589, "lng": -73.9851}
        },
        "stops": []
    },
    "deliveryWindow": {
        "startDate": "2025-10-26T09:00:00",
        "endDate": "2025-10-26T17:00:00"
    }
}

print("Testing POST /api/optimize-route...")
response = requests.post(url, json=data)

print(f"Status Code: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}")
