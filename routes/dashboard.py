from flask import Blueprint, request, jsonify
import json
from datetime import datetime, timedelta
from services.fuel_calculator import FuelCalculator
from services.safety_scorer import SafetyScorer

# Create blueprint
bp = Blueprint('dashboard', __name__)

# Initialize services
fuel_calculator = FuelCalculator()
safety_scorer = SafetyScorer()

@bp.route('/dashboard/overview', methods=['GET'])
def dashboard_overview():
    """
    Get overall fleet dashboard metrics
    """
    try:
        # Load mock data
        vehicles = load_vehicles()
        traffic_data, weather_data = load_conditions()
        
        # Calculate fleet metrics
        active_vehicles = [v for v in vehicles if v.get('status') == 'active']
        
        # Mock routes for active vehicles
        mock_routes = generate_fleet_routes(active_vehicles)
        
        # Calculate aggregated metrics
        fleet_fuel_metrics = fuel_calculator.calculate_fleet_metrics(vehicles, mock_routes)
        
        # Calculate average safety across fleet
        total_safety = 0
        safety_alerts = []
        
        for route in mock_routes:
            route['weather'] = weather_data.get('current_conditions', {})
            route['traffic'] = traffic_data.get('overall_metrics', {})
            safety_data = safety_scorer.calculate_route_safety_score(route)
            total_safety += safety_data['safety_score']
            
            if safety_data['safety_score'] < 60:
                safety_alerts.append({
                    'vehicle_id': route.get('vehicle_id'),
                    'safety_score': safety_data['safety_score'],
                    'alert_level': safety_data['driver_alert_level']
                })
        
        avg_safety = total_safety / len(mock_routes) if mock_routes else 0
        
        # Prepare dashboard data
        dashboard_data = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'fleet_overview': {
                'total_vehicles': len(vehicles),
                'active_vehicles': len(active_vehicles),
                'vehicles_in_transit': len(active_vehicles),  # Mock all active as in transit
                'vehicles_idle': 0
            },
            'fuel_metrics': {
                'total_fuel_gallons_today': fleet_fuel_metrics['total_fuel_gallons'],
                'total_fuel_cost_today': fleet_fuel_metrics['total_fuel_cost'],
                'average_mpg': fleet_fuel_metrics['average_mpg'],
                'cost_per_mile': fleet_fuel_metrics['cost_per_mile'],
                'total_co2_emissions_kg': fleet_fuel_metrics['total_co2_emissions_kg']
            },
            'safety_metrics': {
                'fleet_safety_score': round(avg_safety, 1),
                'safety_level': get_safety_level(avg_safety),
                'vehicles_with_alerts': len(safety_alerts),
                'safety_alerts': safety_alerts[:5]  # Top 5 alerts
            },
            'environmental_conditions': {
                'weather': weather_data.get('current_conditions', {}).get('conditions'),
                'visibility_miles': weather_data.get('current_conditions', {}).get('visibility_miles'),
                'precipitation': weather_data.get('current_conditions', {}).get('precipitation_type'),
                'road_conditions': weather_data.get('current_conditions', {}).get('road_condition')
            },
            'traffic_overview': {
                'average_congestion': traffic_data.get('overall_metrics', {}).get('average_congestion'),
                'total_incidents': traffic_data.get('overall_metrics', {}).get('total_incidents'),
                'average_delay_minutes': 12  # Mock value
            },
            'cost_savings': {
                'fuel_saved_today_gallons': 8.5,  # Mock
                'money_saved_today': 29.75,  # Mock
                'co2_reduced_kg': 32.1  # Mock
            }
        }
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to load dashboard data'
        }), 500

@bp.route('/dashboard/performance', methods=['GET'])
def performance_metrics():
    """
    Get detailed performance metrics and trends
    """
    try:
        # Time period from query params
        period = request.args.get('period', 'week')  # day, week, month
        
        # Generate mock historical data
        historical_data = generate_historical_data(period)
        
        # Calculate trends
        fuel_trend = calculate_trend(historical_data['fuel_consumption'])
        safety_trend = calculate_trend(historical_data['safety_scores'])
        cost_trend = calculate_trend(historical_data['costs'])
        
        return jsonify({
            'success': True,
            'period': period,
            'performance_data': {
                'fuel_efficiency': {
                    'current_avg_mpg': 18.5,
                    'previous_avg_mpg': 17.2,
                    'trend': fuel_trend,
                    'improvement_percentage': 7.6,
                    'historical_data': historical_data['fuel_consumption']
                },
                'safety_performance': {
                    'current_score': 78.5,
                    'previous_score': 75.2,
                    'trend': safety_trend,
                    'incidents_prevented': 3,  # Mock
                    'historical_data': historical_data['safety_scores']
                },
                'cost_analysis': {
                    'total_fuel_cost': sum(historical_data['costs']),
                    'average_daily_cost': sum(historical_data['costs']) / len(historical_data['costs']),
                    'trend': cost_trend,
                    'historical_data': historical_data['costs']
                },
                'route_optimization': {
                    'routes_optimized': 156,  # Mock
                    'average_time_saved_minutes': 8.3,
                    'average_fuel_saved_gallons': 2.1
                }
            },
            'recommendations': [
                "Schedule maintenance for TRK-002 - fuel efficiency declining",
                "Consider route adjustments during morning rush hour",
                "Weather alert: Rain expected tomorrow - adjust safety protocols"
            ]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to load performance metrics'
        }), 500

@bp.route('/dashboard/alerts', methods=['GET'])
def get_alerts():
    """
    Get active alerts and notifications
    """
    try:
        # Load current conditions
        traffic_data, weather_data = load_conditions()
        
        alerts = []
        
        # Weather alerts
        if weather_data.get('current_conditions', {}).get('precipitation_intensity', 0) > 0.5:
            alerts.append({
                'id': 'alert_001',
                'type': 'weather',
                'severity': 'high',
                'title': 'Heavy Rain Warning',
                'message': 'Heavy rainfall detected - all drivers should reduce speed',
                'timestamp': datetime.now().isoformat(),
                'affected_vehicles': ['all']
            })
        
        # Traffic alerts
        if traffic_data.get('overall_metrics', {}).get('total_incidents', 0) > 1:
            alerts.append({
                'id': 'alert_002',
                'type': 'traffic',
                'severity': 'medium',
                'title': 'Multiple Traffic Incidents',
                'message': f"{traffic_data['overall_metrics']['total_incidents']} incidents on major routes",
                'timestamp': datetime.now().isoformat(),
                'affected_routes': ['US-101', 'I-280']
            })
        
        # Hazard zones
        for zone in weather_data.get('hazard_zones', []):
            alerts.append({
                'id': f"alert_{zone['zone_id']}",
                'type': 'hazard',
                'severity': zone['severity'],
                'title': f"Hazard Zone: {zone['hazard_type'].replace('_', ' ').title()}",
                'message': zone['description'],
                'location': zone['location'],
                'radius_miles': zone['radius_miles'],
                'timestamp': datetime.now().isoformat()
            })
        
        # Vehicle-specific alerts (mock)
        alerts.append({
            'id': 'alert_vehicle_001',
            'type': 'vehicle',
            'severity': 'low',
            'title': 'Maintenance Reminder',
            'message': 'TRK-004 due for oil change in 500 miles',
            'vehicle_id': 'TRK-004',
            'timestamp': datetime.now().isoformat()
        })
        
        # Sort by severity
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        alerts.sort(key=lambda x: severity_order.get(x['severity'], 3))
        
        return jsonify({
            'success': True,
            'total_alerts': len(alerts),
            'alerts': alerts,
            'summary': {
                'high_severity': len([a for a in alerts if a['severity'] == 'high']),
                'medium_severity': len([a for a in alerts if a['severity'] == 'medium']),
                'low_severity': len([a for a in alerts if a['severity'] == 'low'])
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to load alerts'
        }), 500

@bp.route('/dashboard/driver-scores', methods=['GET'])
def driver_scores():
    """
    Get driver performance and safety scores
    """
    try:
        vehicles = load_vehicles()
        
        driver_data = []
        for vehicle in vehicles:
            if vehicle.get('status') == 'active':
                # Mock driver scores
                driver_id = vehicle.get('driver_id', 'Unknown')
                driver_data.append({
                    'driver_id': driver_id,
                    'vehicle_id': vehicle['vehicle_id'],
                    'safety_score': 75 + (hash(driver_id) % 20),  # Mock 75-95
                    'fuel_efficiency_score': 70 + (hash(driver_id + 'fuel') % 25),  # Mock 70-95
                    'on_time_percentage': 85 + (hash(driver_id + 'time') % 15),  # Mock 85-100
                    'total_miles_today': 125 + (hash(driver_id + 'miles') % 100),  # Mock
                    'incidents_last_30_days': hash(driver_id + 'incidents') % 3,  # Mock 0-2
                    'ranking': 0  # Will be set after sorting
                })
        
        # Calculate overall score and sort
        for driver in driver_data:
            driver['overall_score'] = (
                driver['safety_score'] * 0.4 +
                driver['fuel_efficiency_score'] * 0.3 +
                driver['on_time_percentage'] * 0.3
            )
        
        driver_data.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Add rankings
        for i, driver in enumerate(driver_data):
            driver['ranking'] = i + 1
        
        return jsonify({
            'success': True,
            'total_drivers': len(driver_data),
            'driver_scores': driver_data,
            'top_performers': driver_data[:3],
            'needs_coaching': [d for d in driver_data if d['safety_score'] < 80]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to load driver scores'
        }), 500

# Helper functions

def load_vehicles():
    """Load vehicle data"""
    try:
        with open('data/vehicles.json', 'r') as f:
            return json.load(f)
    except:
        return []

def load_conditions():
    """Load traffic and weather data"""
    traffic_data = {}
    weather_data = {}
    
    try:
        with open('data/mock_traffic.json', 'r') as f:
            traffic_data = json.load(f)
    except:
        pass
    
    try:
        with open('data/mock_weather.json', 'r') as f:
            weather_data = json.load(f)
    except:
        pass
    
    return traffic_data, weather_data

def generate_fleet_routes(vehicles):
    """Generate mock routes for fleet vehicles"""
    routes = []
    base_distance = 45
    
    for vehicle in vehicles:
        routes.append({
            'vehicle_id': vehicle['vehicle_id'],
            'route_id': f"route_{vehicle['vehicle_id']}",
            'distance_miles': base_distance + (hash(vehicle['vehicle_id']) % 20),
            'duration_minutes': 50 + (hash(vehicle['vehicle_id']) % 30),
            'city_driving_percentage': 30 + (hash(vehicle['vehicle_id']) % 40),
            'average_speed_mph': 45 + (hash(vehicle['vehicle_id']) % 20)
        })
    
    return routes

def get_safety_level(score):
    """Convert score to safety level"""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    elif score >= 40:
        return "Poor"
    else:
        return "Hazardous"

def generate_historical_data(period):
    """Generate mock historical data"""
    if period == 'day':
        days = 1
        points = 24  # Hourly
    elif period == 'week':
        days = 7
        points = 7  # Daily
    else:  # month
        days = 30
        points = 30  # Daily
    
    import random
    
    return {
        'fuel_consumption': [15 + random.random() * 5 for _ in range(points)],
        'safety_scores': [75 + random.random() * 15 for _ in range(points)],
        'costs': [250 + random.random() * 100 for _ in range(points)]
    }

def calculate_trend(data):
    """Calculate trend from data points"""
    if len(data) < 2:
        return 'stable'
    
    # Simple trend calculation
    first_half = sum(data[:len(data)//2]) / (len(data)//2)
    second_half = sum(data[len(data)//2:]) / (len(data) - len(data)//2)
    
    change = (second_half - first_half) / first_half * 100
    
    if change > 5:
        return 'improving'
    elif change < -5:
        return 'declining'
    else:
        return 'stable'