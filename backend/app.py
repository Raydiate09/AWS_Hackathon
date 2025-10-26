from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from tomtom_service import get_tomtom_route
import csv

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
table = dynamodb.Table("optimizedRoute")  # type: ignore

# Claude model ID
model_id = "global.anthropic.claude-haiku-4-5-20251001-v1:0"

def invoke_claude(prompt):
    """Invoke Claude with a prompt"""
    body = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "anthropic_version": "bedrock-2023-05-31"
    })

    try:
        print(f"Invoking Claude with prompt: {prompt[:100]}...")
        response = bedrock.invoke_model(modelId=model_id, body=body)
        response_body = json.loads(response['body'].read())
        result = response_body['content'][0]['text']
        print(f"Claude response received: {result[:100]}...")
        return result
    except Exception as e:
        print(f"Error invoking Claude: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generating AI response: {str(e)}"

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
    try:
        data = request.get_json()
        print(f"Received optimize-route request: {data}")

        user_id = data.get('userId')
        route = data.get('route', {})
        delivery_window = data.get('deliveryWindow', {})

        origin_addr = route.get('origin', {}).get('address', 'Unknown')
        dest_addr = route.get('destination', {}).get('address', 'Unknown')
        stops = route.get('stops', [])
        
        print(f"Route: {origin_addr} -> {dest_addr} with {len(stops)} stops")

        # Create a prompt for Claude
        prompt = f"""
Optimize this delivery route:

Origin: {origin_addr}
Destination: {dest_addr}
Number of Stops: {len(stops)}
Delivery Window: {delivery_window.get('startDate')} to {delivery_window.get('endDate')}

Please provide:
1. Recommended departure time
2. Traffic considerations
3. Weather considerations  
4. Route optimization tips
5. Estimated delivery time

Keep the response concise and actionable.
"""

        print("Calling Claude API...")
        claude_response = invoke_claude(prompt)
        print(f"Claude response length: {len(claude_response)} characters")

        # Mock response structure
        response_data = {
            "success": True,
            "data": {
                "requestId": f"req_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "optimizedRoute": {
                    "origin": route.get('origin'),
                    "destination": route.get('destination'),
                    "stops": stops,
                    "recommendedDepartureTime": delivery_window.get('startDate'),
                    "estimatedArrivalTime": delivery_window.get('endDate')
                },
                "metrics": {
                    "distance": 50.5,  # Mock - calculate real distance
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

        print("Sending response to frontend")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in optimize_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

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

@app.route('/api/tomtom-route', methods=['POST'])
def tomtom_route():
    """Get optimized route from TomTom API"""
    try:
        data = request.get_json()
        print(f"TomTom route request: {data}")
        
        route = data.get('route', {})
        origin = route.get('origin', {}).get('coordinates', {})
        destination = route.get('destination', {}).get('coordinates', {})
        stops = route.get('stops', [])
        
        result = get_tomtom_route(
            origin.get('lat'),
            origin.get('lng'),
            destination.get('lat'),
            destination.get('lng'),
            stops
        )
        
        if result['success']:
            return jsonify({
                "success": True,
                "coordinates": result['coordinates'],
                "summary": result.get('summary', {})
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        print(f"Error in tomtom_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
@app.route('/api/crash-data', methods=['GET'])
def get_crash_data():
    try:
        with open('../crashdata2022-present.csv', 'r') as f:
            reader = csv.DictReader(f)
            records = list(reader)[:100]
        return jsonify({
            "success": True,
            "data": records
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)