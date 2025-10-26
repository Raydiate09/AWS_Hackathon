from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import os
import json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# AWS clients
bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# DynamoDB table
table = dynamodb.Table("optimizedRoute")

# Claude model ID
model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

def invoke_claude(prompt):
    """Invoke Claude with a prompt"""
    body = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "anthropic_version": "bedrock-2023-05-31"
    })

    try:
        response = bedrock.invoke_model(modelId=model_id, body=body)
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
    except Exception as e:
        print(f"Error invoking Claude: {e}")
        return "Error generating response"

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "success": True,
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "dynamodb": "connected",
            "bedrock": "connected"
        }
    })

@app.route('/api/optimize-route', methods=['POST'])
def optimize_route():
    data = request.get_json()

    user_id = data.get('userId')
    route = data.get('route', {})
    delivery_window = data.get('deliveryWindow', {})

    # Create a prompt for Claude
    prompt = f"""
    Optimize the delivery route for user {user_id}.
    Origin: {route.get('origin', {}).get('address', 'Unknown')}
    Destination: {route.get('destination', {}).get('address', 'Unknown')}
    Stops: {len(route.get('stops', []))}
    Delivery window: {delivery_window.get('startDate')} to {delivery_window.get('endDate')}

    Provide an optimized route plan with recommendations.
    """

    claude_response = invoke_claude(prompt)

    # Mock response structure
    response_data = {
        "success": True,
        "data": {
            "requestId": f"req_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "optimizedRoute": {
                "origin": route.get('origin'),
                "destination": route.get('destination'),
                "stops": route.get('stops', []),
                "recommendedDepartureTime": delivery_window.get('startDate'),
                "estimatedArrivalTime": delivery_window.get('endDate')
            },
            "metrics": {
                "distance": 50.5,  # Mock
                "estimatedTime": "2 hours",
                "scores": {
                    "weather": 85,
                    "traffic": 90,
                    "sunlight": 95,
                    "overall": 90
                }
            },
            "recommendations": [claude_response],
            "departureTime": delivery_window.get('startDate'),
            "arrivalTime": delivery_window.get('endDate')
        }
    }

    return jsonify(response_data)

@app.route('/api/request/<request_id>', methods=['GET'])
def get_request(request_id):
    # Mock data - in real implementation, query DynamoDB
    mock_request = {
        "requestId": request_id,
        "userId": "user123",
        "status": "completed",
        "route": {
            "origin": {"address": "Start", "coordinates": {"lat": 0, "lng": 0}},
            "destination": {"address": "End", "coordinates": {"lat": 1, "lng": 1}}
        }
    }

    return jsonify({
        "success": True,
        "data": {
            "request": mock_request,
            "metrics": {"distance": 50.5, "time": "2h"},
            "evaluation": {"score": 90, "feedback": "Good route"}
        }
    })

@app.route('/api/user/<user_id>/requests', methods=['GET'])
def get_user_requests(user_id):
    # Mock data
    mock_requests = [
        {
            "requestId": f"req_{user_id}_1",
            "status": "completed",
            "createdAt": datetime.now().isoformat()
        }
    ]

    return jsonify({
        "success": True,
        "data": {
            "requests": mock_requests,
            "nextKey": None
        }
    })

@app.route('/api/request/<request_id>/reoptimize', methods=['POST'])
def reoptimize_route(request_id):
    data = request.get_json()
    constraints = data.get('constraints', {})

    # Mock re-optimization
    return jsonify({
        "success": True,
        "data": {
            "optimizedRoute": {"message": "Re-optimized"},
            "message": "Route successfully re-optimized"
        }
    })

@app.route('/api/request/<request_id>/status', methods=['GET'])
def get_request_status(request_id):
    # Mock status
    return jsonify({
        "success": True,
        "data": {
            "status": "completed",
            "progress": 100
        }
    })

@app.route('/api/validate-route', methods=['POST'])
def validate_route():
    data = request.get_json()
    route = data.get('route', {})

    # Simple validation
    validation = {
        "isValid": True,
        "warnings": ["Route looks good"],
        "errors": []
    }

    return jsonify({
        "success": True,
        "data": validation
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)