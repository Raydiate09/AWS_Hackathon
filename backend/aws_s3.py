import boto3
import os
import json
from dotenv import load_dotenv

# Load AWS credentials
load_dotenv()

bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# Define the model ID for Claude 3 Sonnet
model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

# Define the prompt
prompt = "Hello, Claude! Can you tell me a short joke?"

# Prepare the request body
body = json.dumps({
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ],
    "max_tokens": 1000,
    "anthropic_version": "bedrock-2023-05-31"
})

# Invoke the model
try:
    response = bedrock.invoke_model(
        modelId=model_id,
        body=body
    )

    # Parse the response
    response_body = json.loads(response['body'].read())
    output_text = response_body['content'][0]['text']

    print("Claude's response:")
    print(output_text)

except Exception as e:
    print(f"Error invoking model: {e}")