from flask import Blueprint, request, jsonify
import json
import os
from services.bedrock_service import BedrockService
from services.fuel_calculator import FuelCalculator
from services.safety_scorer import SafetyScorer

# Create blueprint
bp = Blueprint('optimize', __name__)

# Initialize services
bedrock_service = BedrockService()
fuel_calculator = FuelCalculator()
safety_scorer = SafetyScorer()

# Load mock data
def load_mock_data():
    """Load mock traffic and weather data"""
    traffic_data = {}
    weather_data = {}
    
    try:
        with open('data/mock_traffic.json', 'r') as f:
            traffic_data = json.load(f)
    except:
        print("Warning: Could not load mock traffic data")
    
    try:
        with open('data/mock_weather.json', 'r') as f:
            weather_data = json.load(f)
    except:
        print("Warning: Could not load mock weather data")
    
    return traffic_data, weather_data

@bp.route('/optimize-route', methods=['POST'])
def optimize_route():
    """
    Main route optimization endpoint
    Balances safety and fuel efficiency using AI
    """
    try:
        data = request.json
        
        # Extract parameters
        origin = data.get('origin', {'lat': 37.7749, 'lng': -122.4194})
        destination = data.get('destination', {'lat': 37.3382, 'lng': -121.8863})
        vehicle_id = data.get('vehicle_id', 'TRK-001')
        priority = data.get('priority', 'balanced')  # balanced, safety, fuel_efficiency
        
        # Load mock data for now (in production, this would call real APIs)
        traffic_data, weather_data = load_mock_data()
        
        # Generate mock routes (in production, this would use a routing API)
        routes = generate_mock_routes(origin, destination, traffic_data, weather_data)
        
        # Get vehicle data
        vehicle_data = get_vehicle_data(vehicle_id)
        
        # Analyze each route
        analyzed_routes = []
        for route in routes:
            # Calculate safety score
            safety_analysis = safety_scorer.calculate_route_safety_score(route)
            
            # Calculate fuel consumption
            fuel_analysis = fuel_calculator.calculate_fuel_consumption(route, vehicle_data)
            
            # Combine analyses
            route['safety_analysis'] = safety_analysis
            route['fuel_analysis'] = fuel_analysis
            
            # Calculate combined score based on priority
            route['combined_score'] = calculate_combined_score(
                safety_analysis['safety_score'],
                fuel_analysis['efficiency_factors'],
                priority
            )
            
            analyzed_routes.append(route)
        
        # Prepare data for AI optimization
        route_data = {
            'origin': f"{origin['lat']}, {origin['lng']}",
            'destination': f"{destination['lat']}, {destination['lng']}",
            'vehicle_type': vehicle_data.get('type', 'delivery_van'),
            'cargo_weight': vehicle_data.get('cargo_weight_lbs', 2500),
            'priority': priority,
            'weather': weather_data.get('current_conditions', {}),
            'traffic': traffic_data.get('overall_metrics', {}),
            'routes': analyzed_routes
        }
        
        # Get AI recommendation
        ai_recommendation = bedrock_service.optimize_route(route_data)
        
        # Find the recommended route
        recommended_route = None
        for route in analyzed_routes:
            if route['route_id'] == ai_recommendation.get('recommended_route_id'):
                recommended_route = route
                break
        
        # Prepare response
        response_data = {
            'success': True,
            'recommendation': {
                'route_id': ai_recommendation.get('recommended_route_id'),
                'route_details': recommended_route,
                'safety_score': ai_recommendation.get('safety_score', 75),
                'fuel_efficiency_score': ai_recommendation.get('fuel_efficiency_score', 75),
                'estimated_fuel_gallons': ai_recommendation.get('estimated_fuel_gallons', 0),
                'estimated_time_minutes': ai_recommendation.get('estimated_time_minutes', 0),
                'risk_factors': ai_recommendation.get('risk_factors', []),
                'reasoning': ai_recommendation.get('optimization_reasoning', ''),
                'ai_confidence': ai_recommendation.get('ai_confidence', 0.8)
            },
            'alternatives': analyzed_routes,
            'optimization_factors': {
                'weather_impact': weather_data.get('current_conditions', {}).get('conditions'),
                'traffic_level': traffic_data.get('overall_metrics', {}).get('average_congestion'),
                'priority_mode': priority
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to optimize route'
        }), 500

@bp.route('/compare-routes', methods=['POST'])
def compare_routes():
    """
    Compare multiple routes for safety and fuel efficiency
    """
    try:
        data = request.json
        routes = data.get('routes', [])
        vehicle_id = data.get('vehicle_id', 'TRK-001')
        
        if not routes:
            return jsonify({
                'success': False,
                'message': 'No routes provided for comparison'
            }), 400
        
        # Get vehicle data
        vehicle_data = get_vehicle_data(vehicle_id)
        
        # Load current conditions
        traffic_data, weather_data = load_mock_data()
        
        # Enrich routes with current conditions
        for route in routes:
            route['weather'] = weather_data.get('current_conditions', {})
            route['traffic'] = traffic_data.get('overall_metrics', {})
        
        # Compare safety
        safety_comparison = safety_scorer.compare_routes_safety(routes)
        
        # Compare fuel efficiency
        fuel_comparison = fuel_calculator.compare_routes_fuel_efficiency(routes, vehicle_data)
        
        # Combine comparisons
        combined_comparison = []
        for i, route in enumerate(routes):
            safety_data = next((s for s in safety_comparison if s['route_id'] == route.get('route_id')), {})
            fuel_data = next((f for f in fuel_comparison if f['route_id'] == route.get('route_id')), {})
            
            combined_comparison.append({
                'route_id': route.get('route_id'),
                'route_name': route.get('name', f'Route {i+1}'),
                'distance_miles': route.get('distance_miles', 0),
                'duration_minutes': route.get('duration_minutes', 0),
                'safety_score': safety_data.get('safety_score', 0),
                'safety_rank': safety_data.get('safety_rank', 0),
                'fuel_gallons': fuel_data.get('fuel_gallons', 0),
                'fuel_cost': fuel_data.get('fuel_cost', 0),
                'efficiency_rank': fuel_data.get('efficiency_rank', 0),
                'combined_score': (
                    safety_data.get('safety_score', 0) * 0.5 + 
                    fuel_data.get('efficiency_score', 0) * 0.5
                )
            })
        
        # Sort by combined score
        combined_comparison.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'comparison': combined_comparison,
            'best_for_safety': safety_comparison[0] if safety_comparison else None,
            'best_for_fuel': fuel_comparison[0] if fuel_comparison else None,
            'best_overall': combined_comparison[0] if combined_comparison else None
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to compare routes'
        }), 500

@bp.route('/real-time-updates', methods=['POST'])
def real_time_updates():
    """
    Get real-time updates for an active route
    """
    try:
        data = request.json
        route_id = data.get('route_id')
        current_location = data.get('current_location')
        
        # Load current conditions
        traffic_data, weather_data = load_mock_data()
        
        # Check for new hazards (mock)
        hazards = []
        if weather_data.get('hazard_zones'):
            for zone in weather_data['hazard_zones']:
                # Check if hazard is near current location (simplified)
                hazards.append({
                    'type': zone.get('hazard_type'),
                    'severity': zone.get('severity'),
                    'description': zone.get('description'),
                    'distance_miles': 5.2  # Mock distance
                })
        
        # Calculate updated safety score
        route_data = {
            'weather': weather_data.get('current_conditions', {}),
            'traffic': traffic_data.get('overall_metrics', {}),
            'hazard_zones': weather_data.get('hazard_zones', [])
        }
        
        safety_update = safety_scorer.calculate_route_safety_score(route_data)
        
        # Prepare alerts
        alerts = []
        if safety_update['safety_score'] < 50:
            alerts.append({
                'type': 'safety',
                'severity': 'high',
                'message': 'Route safety has degraded - consider alternative route'
            })
        
        for hazard in hazards:
            if hazard['severity'] == 'high':
                alerts.append({
                    'type': 'hazard',
                    'severity': 'high',
                    'message': f"Warning: {hazard['description']} ahead"
                })
        
        return jsonify({
            'success': True,
            'route_id': route_id,
            'current_safety_score': safety_update['safety_score'],
            'current_conditions': {
                'weather': weather_data.get('current_conditions', {}).get('conditions'),
                'visibility': weather_data.get('current_conditions', {}).get('visibility_miles'),
                'traffic': traffic_data.get('overall_metrics', {}).get('average_congestion')
            },
            'upcoming_hazards': hazards,
            'alerts': alerts,
            'recommendations': safety_update['safety_recommendations'][:3]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to get real-time updates'
        }), 500

# Helper functions

def generate_mock_routes(origin, destination, traffic_data, weather_data):
    """Generate mock routes for testing"""
    
    # Mock 3 different routes
    return [
        {
            'route_id': 'route_1',
            'name': 'I-280 Direct',
            'distance_miles': 45.2,
            'duration_minutes': 52,
            'city_driving_percentage': 30,
            'average_speed_mph': 52,
            'elevation_gain_ft': 250,
            'weather': weather_data.get('current_conditions', {}),
            'traffic': {
                'congestion_level': 'moderate',
                'incidents': 1,
                'average_speed_mph': 52
            },
            'road_conditions': {
                'surface_condition': weather_data.get('current_conditions', {}).get('road_condition', 'dry'),
                'road_type': 'highway'
            }
        },
        {
            'route_id': 'route_2',
            'name': 'US-101 Scenic',
            'distance_miles': 52.8,
            'duration_minutes': 68,
            'city_driving_percentage': 45,
            'average_speed_mph': 46,
            'elevation_gain_ft': 450,
            'weather': weather_data.get('current_conditions', {}),
            'traffic': {
                'congestion_level': 'heavy',
                'incidents': 2,
                'average_speed_mph': 35
            },
            'road_conditions': {
                'surface_condition': weather_data.get('current_conditions', {}).get('road_condition', 'wet'),
                'road_type': 'highway',
                'construction_zones': 1
            }
        },
        {
            'route_id': 'route_3',
            'name': 'CA-85 Express',
            'distance_miles': 48.5,
            'duration_minutes': 55,
            'city_driving_percentage': 25,
            'average_speed_mph': 58,
            'elevation_gain_ft': 180,
            'weather': weather_data.get('current_conditions', {}),
            'traffic': {
                'congestion_level': 'light',
                'incidents': 0,
                'average_speed_mph': 62
            },
            'road_conditions': {
                'surface_condition': weather_data.get('current_conditions', {}).get('road_condition', 'dry'),
                'road_type': 'highway'
            }
        }
    ]

def get_vehicle_data(vehicle_id):
    """Get vehicle data from mock data"""
    try:
        with open('data/vehicles.json', 'r') as f:
            vehicles = json.load(f)
            for vehicle in vehicles:
                if vehicle.get('vehicle_id') == vehicle_id:
                    return vehicle
    except:
        pass
    
    # Default vehicle if not found
    return {
        'vehicle_id': vehicle_id,
        'type': 'delivery_van',
        'mpg_city': 16,
        'mpg_highway': 22,
        'fuel_capacity_gallons': 25,
        'cargo_weight_lbs': 2500
    }

def calculate_combined_score(safety_score, efficiency_factors, priority):
    """Calculate combined score based on priority"""
    
    # Calculate efficiency score from factors
    efficiency_score = 100
    for factor, impact in efficiency_factors.items():
        efficiency_score -= abs(impact)
    efficiency_score = max(0, efficiency_score)
    
    # Weight based on priority
    if priority == 'safety':
        return safety_score * 0.7 + efficiency_score * 0.3
    elif priority == 'fuel_efficiency':
        return safety_score * 0.3 + efficiency_score * 0.7
    else:  # balanced
        return safety_score * 0.5 + efficiency_score * 0.5