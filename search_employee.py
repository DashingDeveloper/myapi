import os
import pymysql
import json
import numpy as np
import face_recognition
from fastapi import APIRouter, File, UploadFile, HTTPException
from PIL import Image
from io import BytesIO

search_router = APIRouter()

# Database connection function
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

@search_router.post("/search_employee/")
async def search_employee(file: UploadFile = File(...)):
    try:
        # Read the uploaded image
        image = Image.open(BytesIO(await file.read())).convert("RGB")
        image = np.array(image, dtype=np.uint8)

        # Encode the uploaded image
        uploaded_face_encodings = face_recognition.face_encodings(image)
        if not uploaded_face_encodings:
            raise HTTPException(status_code=400, detail="No face detected in the uploaded image.")

        uploaded_encoding = uploaded_face_encodings[0]

        # Fetch stored face encodings from the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, id, department, face_encoding FROM employees")
        employees = cursor.fetchall()
        cursor.close()
        conn.close()

        for name, user_id, department, stored_encoding_json in employees:
            stored_encoding = np.array(json.loads(stored_encoding_json))

            # Compare the uploaded encoding with stored encodings
            match = face_recognition.compare_faces([stored_encoding], uploaded_encoding, tolerance=0.5)

            if match[0]:  # If True, we found a match
                return {
                    "message": "Employee Found",
                    "name": name,
                    "user_id": user_id,
                    "department": department
                }

        return {"message": "Employee not found"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
