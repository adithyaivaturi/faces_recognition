from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import face_recognition
import pandas as pd
from sqlalchemy import create_engine
import pyodbc
import os
import shutil
from tempfile import NamedTemporaryFile

app = Flask(__name__)

# Define the connection string for SQL Server using pyodbc
conn_str = (
    r'DRIVER={SQL Server};'
    r'SERVER=DESKTOP-QCOS2KB\SQLEXPRESS;'
    r'DATABASE=python project;'
    r'Trusted_Connection=yes;'
)

# Create SQLAlchemy engine
engine = create_engine('mssql+pyodbc://', creator=lambda: pyodbc.connect(conn_str))


@app.route('/compare_faces', methods=['GET'])
def compare_faces():
    try:
        file = request.files['file']

        # Save uploaded file temporarily
        tmp_path = NamedTemporaryFile(delete=False, suffix=".jpg").name
        file.save(tmp_path)

        # Load and encode unknown face
        unknown_image = face_recognition.load_image_file(tmp_path)
        unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

        # Get face recognition data from SQL Server
        data = get_face_recognition_data()

        for i in data:
            known_image = face_recognition.load_image_file(i['Photo'])
            known_encoding = face_recognition.face_encodings(known_image)[0]

            # Compare faces
            results = face_recognition.compare_faces([known_encoding], unknown_encoding)

            if results[0]:
                return jsonify({"match": True, "message": "These are the same person.", "Mcode": i["MCode"], "MName": i["MName"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return jsonify({"match": False, "message": "These are different people.", "MCode": "", "MName": ""})
def get_face_recognition_data():
    try:
        query = "SELECT * FROM Face_Recognition"
        df = pd.read_sql(query, con=engine)
        return df.to_dict(orient='records')  # Convert DataFrame to list of dictionaries (JSON serializable)
    except Exception as e:
        return {"error": str(e)}
    finally:
        engine.dispose()  # Dispose the engine
