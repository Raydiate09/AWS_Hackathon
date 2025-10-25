from flask import Blueprint, request, jsonify
import json
from datetime import datetime

# Create blueprint
bp = Blueprint('vehicles', __name__)

@bp.route('/vehicles', methods=['GET'])
def get_vehicles():
    """
    Get all vehicles in the fleet
    """
    try:
        vehicles = load_vehicles()
        
        # Add calculated fields
        for vehicle in vehicles:
            vehicle['fuel_efficiency_rating'] = calculate_efficiency_rating(vehicle)
            vehicle['maintenance_status'] = get_maintenance_status(vehicle)
        
        return jsonify({
            'success': True,
            'total_vehicles': len(vehicles),
            'vehicles': vehicles
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to load vehicles'
        }), 500

@bp.route('/vehicles/<vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    """
    Get details for a specific vehicle
    """
    try:
        vehicles = load_vehicles()
        vehicle = next((v for v in vehicles if v['vehicle_id'] == vehicle_id), None)
        
        if not vehicle:
            return jsonify({
                'success': False,
                'message': f'Vehicle {vehicle_id} not found'
            }), 404
        
        # Add detailed information
        vehicle['fuel_efficiency_rating'] = calculate_efficiency_rating(vehicle)
        vehicle['maintenance_status'] = get_maintenance_status(vehicle)
        vehicle['current_location'] = get_mock_location(vehicle_id)
        vehicle['today_stats'] = get_today_stats(vehicle_id)
        
        return jsonify({
            'success': True,
            'vehicle': vehicle
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to load vehicle details'
        }), 500

@bp.route('/vehicles/<vehicle_id>/update', methods=['POST'])
def update_vehicle(vehicle_id):
    """
    Update vehicle information
    """
    try:
        data = request.json
        vehicles = load_vehicles()
        
        # Find and update vehicle
        vehicle_index = next((i for i, v in enumerate(vehicles) if v['vehicle_id'] == vehicle_id), None)
        
        if vehicle_index is None:
            return jsonify({
                'success': False,
                'message': f'Vehicle {vehicle_id} not found'
            }), 404
        
        # Update fields
        for key, value in data.items():
            if key not in ['vehicle_id']:  # Don't allow ID changes
                vehicles[vehicle_index][key] = value
        
        # Save back to file
        save_vehicles(vehicles)
        
        return jsonify({
            'success': True,
            'message': f'Vehicle {vehicle_id} updated successfully',
            'vehicle': vehicles[vehicle_index]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to update vehicle'
        }), 500

@bp.route('/vehicles/<vehicle_id>/status', methods=['POST'])
def update_vehicle_status(vehicle_id):
    """
    Update vehicle status (active, maintenance, inactive)
    """
    try:
        data = request.json
        new_status = data.get('status')
        
        if new_status not in ['active', 'maintenance', 'inactive']:
            return jsonify({
                'success': False,
                'message': 'Invalid status. Must be active, maintenance, or inactive'
            }), 400
        
        vehicles = load_vehicles()
        vehicle_index = next((i for i, v in enumerate(vehicles) if v['vehicle_id'] == vehicle_id), None)
        
        if vehicle_index is None:
            return jsonify({
                'success': False,
                'message': f'Vehicle {vehicle_id} not found'
            }), 404
        
        vehicles[vehicle_index]['status'] = new_status
        vehicles[vehicle_index]['status_updated'] = datetime.now().isoformat()
        
        # Save back to file
        save_vehicles(vehicles)
        
        return jsonify({
            'success': True,
            'message': f'Vehicle {vehicle_id} status updated to {new_status}',
            'vehicle': vehicles[vehicle_index]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to update vehicle status'
        }), 500

@bp.route('/vehicles/<vehicle_id>/location', methods=['GET'])
def get_vehicle_location(vehicle_id):
    """
    Get current location of a vehicle
    """
    try:
        # Check vehicle exists
        vehicles = load_vehicles()
        vehicle = next((v for v in vehicles if v['vehicle_id'] == vehicle_id), None)
        
        if not vehicle:
            return jsonify({
                'success': False,
                'message': f'Vehicle {vehicle_id} not found'
            }), 404
        
        # Return mock location
        location = get_mock_location(vehicle_id)
        
        return jsonify({
            'success': True,
            'vehicle_id': vehicle_id,
            'location': location,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to get vehicle location'
        }), 500

@bp.route('/vehicles/fleet-summary', methods=['GET'])
def fleet_summary():
    """
    Get fleet summary statistics
    """
    try:
        vehicles = load_vehicles()
        
        # Calculate statistics
        total_vehicles = len(vehicles)
        active_vehicles = len([v for v in vehicles if v['status'] == 'active'])
        maintenance_vehicles = len([v for v in vehicles if v['status'] == 'maintenance'])
        inactive_vehicles = len([v for v in vehicles if v['status'] == 'inactive'])
        
        # Vehicle types
        vehicle_types = {}
        for vehicle in vehicles:
            vtype = vehicle.get('type', 'unknown')
            vehicle_types[vtype] = vehicle_types.get(vtype, 0) + 1
        
        # Average MPG
        total_city_mpg = sum(v.get('mpg_city', 0) for v in vehicles)
        total_highway_mpg = sum(v.get('mpg_highway', 0) for v in vehicles)
        avg_city_mpg = total_city_mpg / total_vehicles if total_vehicles > 0 else 0
        avg_highway_mpg = total_highway_mpg / total_vehicles if total_vehicles > 0 else 0
        
        return jsonify({
            'success': True,
            'fleet_summary': {
                'total_vehicles': total_vehicles,
                'status_breakdown': {
                    'active': active_vehicles,
                    'maintenance': maintenance_vehicles,
                    'inactive': inactive_vehicles
                },
                'vehicle_types': vehicle_types,
                'fuel_efficiency': {
                    'average_city_mpg': round(avg_city_mpg, 1),
                    'average_highway_mpg': round(avg_highway_mpg, 1)
                },
                'capacity': {
                    'total_cargo_capacity_lbs': sum(v.get('cargo_weight_lbs', 0) for v in vehicles),
                    'total_fuel_capacity_gallons': sum(v.get('fuel_capacity_gallons', 0) for v in vehicles)
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to load fleet summary'
        }), 500

# Helper functions

def load_vehicles():
    """Load vehicles from JSON file"""
    try:
        with open('data/vehicles.json', 'r') as f:
            return json.load(f)
    except:
        return []

def save_vehicles(vehicles):
    """Save vehicles back to JSON file"""
    try:
        with open('data/vehicles.json', 'w') as f:
            json.dump(vehicles, f, indent=2)
        return True
    except:
        return False

def calculate_efficiency_rating(vehicle):
    """Calculate efficiency rating based on MPG"""
    avg_mpg = (vehicle.get('mpg_city', 0) + vehicle.get('mpg_highway', 0)) / 2
    
    if avg_mpg >= 25:
        return 'Excellent'
    elif avg_mpg >= 20:
        return 'Good'
    elif avg_mpg >= 15:
        return 'Fair'
    else:
        return 'Poor'

def get_maintenance_status(vehicle):
    """Get maintenance status (mock)"""
    # Mock implementation - in production would check maintenance records
    vehicle_hash = hash(vehicle['vehicle_id'])
    
    if vehicle_hash % 10 < 7:
        return {
            'status': 'Good',
            'next_service_miles': 2500 + (vehicle_hash % 3000),
            'last_service_date': '2024-09-15'
        }
    else:
        return {
            'status': 'Service Soon',
            'next_service_miles': 500 + (vehicle_hash % 500),
            'last_service_date': '2024-08-01'
        }

def get_mock_location(vehicle_id):
    """Generate mock location for vehicle"""
    # Mock GPS coordinates near San Francisco Bay Area
    base_lat = 37.7749
    base_lng = -122.4194
    
    # Use vehicle_id hash for consistent but different locations
    offset = hash(vehicle_id + str(datetime.now().hour))
    
    return {
        'lat': base_lat + (offset % 100) / 1000,
        'lng': base_lng + ((offset % 200) - 100) / 1000,
        'speed_mph': 35 + (offset % 30),
        'heading': offset % 360,
        'on_route': True,
        'route_id': f'route_{vehicle_id}'
    }

def get_today_stats(vehicle_id):
    """Get today's statistics for a vehicle (mock)"""
    # Mock stats based on vehicle_id
    base_hash = hash(vehicle_id + str(datetime.now().date()))
    
    return {
        'miles_driven': 85 + (base_hash % 100),
        'fuel_consumed_gallons': 4.2 + (base_hash % 30) / 10,
        'stops_completed': 12 + (base_hash % 20),
        'average_speed_mph': 38 + (base_hash % 15),
        'idle_time_minutes': 45 + (base_hash % 60),
        'safety_events': base_hash % 3
    }