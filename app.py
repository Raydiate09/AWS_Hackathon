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
        "version": "1.0.0"
    }), 200

# Test endpoint
@app.route('/api/test', methods=['GET'])
def test():
    """
    Test endpoint to verify API Gateway setup
    """
    return jsonify({
        "message": "API is working!",
        "aws_region": os.getenv('AWS_REGION')
    }), 200

# Import routes (we'll create these next)
# from routes import optimize, vehicles, dashboard
# app.register_blueprint(optimize.bp, url_prefix='/api')
# app.register_blueprint(vehicles.bp, url_prefix='/api')
# app.register_blueprint(dashboard.bp, url_prefix='/api')

if __name__ == '__main__':
    print("=" * 50)
    print("SightLine Backend Starting...")
    print(f"AWS Region: {os.getenv('AWS_REGION')}")
    print(f"Debug Mode: {app.config['DEBUG']}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5003, debug=True)