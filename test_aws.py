import boto3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Testing AWS connection...")
print(f"AWS Region: {os.getenv('AWS_REGION')}")
print(f"Access Key ID: {os.getenv('AWS_ACCESS_KEY_ID')[:10]}...")

try:
    # Test Bedrock connection
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name=os.getenv('AWS_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    print("✓ Successfully connected to AWS Bedrock!")
    
    # Test S3 connection
    s3 = boto3.client(
        service_name='s3',
        region_name=os.getenv('AWS_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    print("✓ Successfully connected to AWS S3!")
    
    print("\n✓✓✓ All AWS connections working! ✓✓✓")
    
except Exception as e:
    print(f"✗ Error connecting to AWS: {e}")
    print("\nTroubleshooting:")
    print("1. Check your AWS credentials in .env file")
    print("2. Verify region is us-west-2")
    print("3. Confirm Bedrock access is enabled in AWS Console")