import boto3
import os
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

table = dynamodb.Table("optimizedRoute")

# 扫描整个表
response = table.scan()

items = response.get("Items", [])
print(f"✅ Retrieved {len(items)} records")
for item in items[:5]:
    print(item)  # 打印前5行