from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
import pyodbc
from fastapi import FastAPI, HTTPException, UploadFile, File
from typing import List
import pandas as pd
from tempfile import NamedTemporaryFile
import shutil
import os
from deepface import DeepFace

# Define the connection string for SQL Server using pyodbc
conn_str = (
    r'DRIVER={SQL Server};'
    r'SERVER=DESKTOP-QCOS2KB\SQLEXPRESS;'
    r'DATABASE=python project;'
    r'Trusted_Connection=yes;'
)

# Create SQLAlchemy engine
engine = create_engine('mssql+pyodbc://', creator=lambda: pyodbc.connect(conn_str))

app = FastAPI()

@app.get("/compare_faces")
async def compare_faces(file: UploadFile = File(...)):
    try:
        with NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Use DeepFace to detect and compare faces
        result = DeepFace.verify(tmp_path, model_name="Facenet", enforce_detection=False)

        match_details = {"match": result["verified"], "message": "", "MCode": "", "MName": ""}

        if result["verified"]:
            match_details["message"] = "These are the same person."
            match_details["MCode"] = result["verified"][0]["MCode"]
            match_details["MName"] = result["verified"][0]["MName"]
        else:
            match_details["message"] = "These are different people."

        return JSONResponse(content=match_details)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'tmp_path' in locals():
            try:
                os.remove(tmp_path)
            except Exception as e:
                pass

def get_face_recognition_data():
    try:
        query = "SELECT * FROM Face_Recognition"
        df = pd.read_sql(query, con=engine)
        return df.to_dict(orient='records')  # Convert DataFrame to list of dictionaries (JSON serializable)
    except Exception as e:
        return {"error": str(e)}
    finally:
        engine.dispose()  # Dispose the engine

