"""
SightLine Backend Test Suite
Run this to test all endpoints and core logic
"""

import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:5003"

# ANSI color codes for pretty output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test_header(test_name):
    print(f"\n{BLUE}{'='*50}{RESET}")
    print(f"{BLUE}Testing: {test_name}{RESET}")
    print(f"{BLUE}{'='*50}{RESET}")

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"{YELLOW}ℹ {message}{RESET}")

def test_health_check():
    """Test the health check endpoint"""
    print_test_header("Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed: {data['message']}")
            print_info(f"Services: {json.dumps(data.get('services', {}), indent=2)}")
            return True
        else:
            print_error(f"Health check failed with status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return False

def test_api_test():
    """Test the API test endpoint"""
    print_test_header("API Test Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/api/test")
        if response.status_code == 200:
            data = response.json()
            print_success(f"API test passed: {data['message']}")
            print_info(f"AWS Region: {data['aws_region']}")
            return True
        else:
            print_error(f"API test failed with status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"API test error: {str(e)}")
        return False

def test_route_optimization():
    """Test the route optimization endpoint"""
    print_test_header("Route Optimization")
    
    payload = {
        "origin": {"lat": 37.7749, "lng": -122.4194},
        "destination": {"lat": 37.3382, "lng": -121.8863},
        "vehicle_id": "TRK-001",
        "priority": "balanced"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/optimize-route", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("Route optimization successful!")
                rec = data.get('recommendation', {})
                print_info(f"Recommended Route: {rec.get('route_id')}")
                print_info(f"Safety Score: {rec.get('safety_score')}/100")
                print_info(f"Fuel Efficiency: {rec.get('fuel_efficiency_score')}/100")
                print_info(f"Est. Fuel: {rec.get('estimated_fuel_gallons')} gallons")
                print_info(f"Est. Time: {rec.get('estimated_time_minutes')} minutes")
                print_info(f"AI Confidence: {rec.get('ai_confidence', 0)*100:.0f}%")
                
                # Show risk factors if any
                risks = rec.get('risk_factors', [])
                if risks:
                    print_info(f"Risk Factors: {', '.join(risks[:3])}")
                
                return True
            else:
                print_error("Route optimization returned success=false")
                return False
        else:
            print_error(f"Route optimization failed with status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Route optimization error: {str(e)}")
        print_info("Note: This might fail if AWS Bedrock is not properly configured")
        return False

def test_route_comparison():
    """Test the route comparison endpoint"""
    print_test_header("Route Comparison")
    
    payload = {
        "vehicle_id": "TRK-001",
        "routes": [
            {
                "route_id": "route_1",
                "name": "Highway Route",
                "distance_miles": 45.2,
                "duration_minutes": 52,
                "city_driving_percentage": 30
            },
            {
                "route_id": "route_2",
                "name": "Scenic Route",
                "distance_miles": 52.8,
                "duration_minutes": 68,
                "city_driving_percentage": 45
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/compare-routes", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("Route comparison successful!")
                
                comparison = data.get('comparison', [])
                for route in comparison[:2]:
                    print_info(f"\n  {route['route_name']}:")
                    print(f"    - Safety Score: {route['safety_score']}")
                    print(f"    - Fuel Needed: {route['fuel_gallons']} gallons")
                    print(f"    - Fuel Cost: ${route['fuel_cost']}")
                    print(f"    - Combined Score: {route['combined_score']:.1f}")
                
                return True
            else:
                print_error("Route comparison returned success=false")
                return False
        else:
            print_error(f"Route comparison failed with status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Route comparison error: {str(e)}")
        return False

def test_vehicles():
    """Test vehicle endpoints"""
    print_test_header("Vehicle Management")
    
    # Test getting all vehicles
    try:
        response = requests.get(f"{BASE_URL}/api/vehicles")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved {data['total_vehicles']} vehicles")
            
            # Test getting specific vehicle
            if data['vehicles']:
                vehicle_id = data['vehicles'][0]['vehicle_id']
                response = requests.get(f"{BASE_URL}/api/vehicles/{vehicle_id}")
                if response.status_code == 200:
                    vehicle = response.json()['vehicle']
                    print_success(f"Retrieved vehicle {vehicle_id}")
                    print_info(f"  Type: {vehicle['type']}")
                    print_info(f"  MPG: City {vehicle['mpg_city']}, Highway {vehicle['mpg_highway']}")
                    print_info(f"  Status: {vehicle['status']}")
                    
                    # Test getting location
                    response = requests.get(f"{BASE_URL}/api/vehicles/{vehicle_id}/location")
                    if response.status_code == 200:
                        location = response.json()['location']
                        print_success(f"Retrieved location for {vehicle_id}")
                        print_info(f"  Position: ({location['lat']:.4f}, {location['lng']:.4f})")
                        print_info(f"  Speed: {location['speed_mph']} mph")
                    
                    return True
        else:
            print_error(f"Failed to get vehicles: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Vehicle test error: {str(e)}")
        return False

def test_dashboard():
    """Test dashboard endpoints"""
    print_test_header("Dashboard")
    
    try:
        # Test dashboard overview
        response = requests.get(f"{BASE_URL}/api/dashboard/overview")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("Dashboard overview loaded")
                
                fleet = data['fleet_overview']
                print_info(f"Fleet Status:")
                print(f"  - Total Vehicles: {fleet['total_vehicles']}")
                print(f"  - Active: {fleet['active_vehicles']}")
                print(f"  - In Transit: {fleet['vehicles_in_transit']}")
                
                fuel = data['fuel_metrics']
                print_info(f"Fuel Metrics:")
                print(f"  - Today's Fuel: {fuel['total_fuel_gallons_today']} gallons")
                print(f"  - Today's Cost: ${fuel['total_fuel_cost_today']}")
                print(f"  - Average MPG: {fuel['average_mpg']}")
                
                safety = data['safety_metrics']
                print_info(f"Safety Metrics:")
                print(f"  - Fleet Safety Score: {safety['fleet_safety_score']}/100")
                print(f"  - Safety Level: {safety['safety_level']}")
                print(f"  - Vehicles with Alerts: {safety['vehicles_with_alerts']}")
                
                # Test alerts
                response = requests.get(f"{BASE_URL}/api/dashboard/alerts")
                if response.status_code == 200:
                    alerts_data = response.json()
                    print_success(f"Retrieved {alerts_data['total_alerts']} alerts")
                    
                    summary = alerts_data['summary']
                    if summary['high_severity'] > 0:
                        print_info(f"  ⚠️  High severity alerts: {summary['high_severity']}")
                    if summary['medium_severity'] > 0:
                        print_info(f"  ⚠️  Medium severity alerts: {summary['medium_severity']}")
                
                return True
            else:
                print_error("Dashboard overview returned success=false")
                return False
        else:
            print_error(f"Dashboard overview failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Dashboard test error: {str(e)}")
        return False

def test_real_time_updates():
    """Test real-time updates endpoint"""
    print_test_header("Real-time Updates")
    
    payload = {
        "route_id": "route_1",
        "current_location": {"lat": 37.5000, "lng": -122.1500}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/real-time-updates", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("Real-time updates retrieved")
                print_info(f"Current Safety Score: {data['current_safety_score']}/100")
                
                conditions = data['current_conditions']
                print_info(f"Current Conditions:")
                print(f"  - Weather: {conditions['weather']}")
                print(f"  - Visibility: {conditions['visibility']} miles")
                print(f"  - Traffic: {conditions['traffic']}")
                
                if data['alerts']:
                    print_info(f"Active Alerts: {len(data['alerts'])}")
                    for alert in data['alerts'][:2]:
                        print(f"  - {alert['severity'].upper()}: {alert['message']}")
                
                return True
        else:
            print_error(f"Real-time updates failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Real-time updates error: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print(f"\n{BLUE}{'='*50}{RESET}")
    print(f"{BLUE}SIGHTLINE BACKEND TEST SUITE{RESET}")
    print(f"{BLUE}{'='*50}{RESET}")
    print(f"Starting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Health Check", test_health_check),
        ("API Test", test_api_test),
        ("Vehicle Management", test_vehicles),
        ("Dashboard", test_dashboard),
        ("Route Comparison", test_route_comparison),
        ("Real-time Updates", test_real_time_updates),
        ("Route Optimization", test_route_optimization),  # Run this last as it may fail
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Unexpected error in {test_name}: {str(e)}")
            results[test_name] = False
    
    # Print summary
    print(f"\n{BLUE}{'='*50}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*50}{RESET}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed in results.items():
        status = f"{GREEN}PASSED{RESET}" if passed else f"{RED}FAILED{RESET}"
        print(f"{test_name}: {status}")
    
    print(f"\n{BLUE}Overall: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"{GREEN}🎉 All tests passed! Backend is fully operational.{RESET}")
    elif passed >= total * 0.7:
        print(f"{YELLOW}⚠️  Most tests passed. Check failed tests for issues.{RESET}")
    else:
        print(f"{RED}❌ Multiple tests failed. Please review configuration.{RESET}")
    
    # Special notes
    if not results.get("Route Optimization"):
        print(f"\n{YELLOW}Note: Route Optimization failed - this is expected if AWS Bedrock{RESET}")
        print(f"{YELLOW}      is not fully configured or if you're using fallback mode.{RESET}")

if __name__ == "__main__":
    # Check if server is running
    print(f"{YELLOW}Checking if Flask server is running...{RESET}")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"{GREEN}✓ Server is running!{RESET}")
        run_all_tests()
    except requests.exceptions.RequestException:
        print(f"{RED}✗ Flask server is not running!{RESET}")
        print(f"{YELLOW}Please start the server first:{RESET}")
        print(f"  cd /path/to/sightline-backend")
        print(f"  source venv/bin/activate")
        print(f"  python app.py")