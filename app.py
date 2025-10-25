from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for frontend communication
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'True') == 'True'

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check to verify API is running
    """
    return jsonify({
        "status": "ok",
        "message": "DTS Backend is running",
        "version": "1.0.0",
        "services": {
            "aws_bedrock": "configured",
            "fuel_calculator": "ready",
            "safety_scorer": "ready"
        }
    }), 200

# Test endpoint
@app.route('/api/test', methods=['GET'])
def test():
    """
    Test endpoint to verify API Gateway setup
    """
    return jsonify({
        "message": "API is working!",
        "aws_region": os.getenv('AWS_REGION'),
        "endpoints_available": True
    }), 200

# Import and register all routes
from routes import optimize, vehicles, dashboard

app.register_blueprint(optimize.bp, url_prefix='/api')
app.register_blueprint(vehicles.bp, url_prefix='/api')
app.register_blueprint(dashboard.bp, url_prefix='/api')

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    """
    Root endpoint with API information
    """
    return jsonify({
        "name": "DTS Backend API",
        "version": "1.0.0",
        "description": "AI-powered fleet route optimization balancing safety and fuel efficiency",
        "team": "Graduate students @ Santa Clara University",
        "hackathon": "AWS x INRIX Hackathon 2025",
        "endpoints": {
            "health": "/health",
            "test": "/api/test",
            "optimize": {
                "POST /api/optimize-route": "Get AI-optimized route recommendation",
                "POST /api/compare-routes": "Compare multiple routes",
                "POST /api/real-time-updates": "Get real-time route updates"
            },
            "vehicles": {
                "GET /api/vehicles": "List all vehicles",
                "GET /api/vehicles/<id>": "Get vehicle details",
                "POST /api/vehicles/<id>/update": "Update vehicle info",
                "POST /api/vehicles/<id>/status": "Update vehicle status",
                "GET /api/vehicles/<id>/location": "Get vehicle location",
                "GET /api/vehicles/fleet-summary": "Get fleet summary"
            },
            "dashboard": {
                "GET /api/dashboard/overview": "Dashboard overview",
                "GET /api/dashboard/performance": "Performance metrics",
                "GET /api/dashboard/alerts": "Active alerts",
                "GET /api/dashboard/driver-scores": "Driver scores"
            }
        }
    }), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚚 DTS Backend Starting...")
    print(f"📍 AWS Region: {os.getenv('AWS_REGION')}")
    print(f"🔧 Debug Mode: {app.config['DEBUG']}")
    print("=" * 50)
    print("📊 Available Endpoints:")
    print("   - Health Check: http://localhost:5003/health")
    print("   - API Test: http://localhost:5003/api/test")
    print("   - Route Optimization: http://localhost:5003/api/optimize-route")
    print("   - Dashboard: http://localhost:5003/api/dashboard/overview")
    print("   - Vehicles: http://localhost:5003/api/vehicles")
    print("=" * 50)
    print("🎯 Key Features:")
    print("   ✓ AI-powered route optimization (AWS Bedrock Claude)")
    print("   ✓ Real-time safety scoring")
    print("   ✓ Fuel efficiency calculations")
    print("   ✓ Weather & traffic integration")
    print("   ✓ Fleet management dashboard")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5003, debug=True)