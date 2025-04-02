import io
import boto3
import pymysql
import face_recognition
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AWS Credentials and Configuration
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX")

# Database Credentials
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Initialize S3 client with credentials
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

# Connect to MySQL database
conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = conn.cursor()

# Get all objects in the S3 bucket under the main folder
response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_PREFIX)

for obj in response.get("Contents", []):
    s3_key = obj["Key"]
    filename = s3_key.split("/")[-1]  # Extract filename

    if filename.endswith((".jpg", ".png")):
        try:
            # Extract name and user_id
            parts = filename.rsplit(".", 1)[0].split("_")
            name = parts[0]
            user_id = int(parts[1]) if len(parts) > 1 else None  # Convert user_id to int if exists

            # Read image from S3 directly into memory
            print(f"Processing {s3_key} from S3...")
            s3_object = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
            image_bytes = s3_object['Body'].read()

            # Load image from memory
            image = face_recognition.load_image_file(io.BytesIO(image_bytes))
            face_encodings = face_recognition.face_encodings(image)

            if face_encodings:
                face_encoding = json.dumps(face_encodings[0].tolist())
            else:
                print(f"No face found in {filename}. Skipping.")
                continue

            # Insert into MySQL (handle NULL user_id)
            cursor.execute(
                "INSERT INTO employees (name, user_id, department, face_encoding) VALUES (%s, %s, %s, %s)",
                (name, user_id, "Unknown", face_encoding)  # Set "Unknown" department for now
            )

        except Exception as e:
            print(f"Error processing {filename}: {e}")

# Commit and close
conn.commit()
cursor.close()
conn.close()

print("Employee data stored successfully!")
