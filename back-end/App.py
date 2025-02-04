from flask import Flask, request, jsonify, Response

import mysql.connector
from mysql.connector import Error

import csv
import io
import os
from functools import wraps
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# In-memory user authentication
users = {"admin": "freepasses4all"}  # Example admin user
sessions = {}  # Store logged-in users

# Utility function to return JSON or CSV
def format_response(data):
    if not data:
        return "", 204
    response_format = request.args.get("format", "json")
    if response_format == "csv":
        df = pd.DataFrame(data)
        output = io.StringIO()
        df.to_csv(output, index=False)
        return Response(output.getvalue(), mimetype='text/csv', headers={"Content-Disposition": "attachment; filename=data.csv"})
    return jsonify(data)


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",       # Change if MySQL is hosted remotely
        user="root",            # Your MySQL username
        password="",            # Your MySQL password
        database="mydb"         # Your MySQL database name
    )

# Authentication middleware
def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("X-OBSERVATORY-AUTH")
        if not token or token not in sessions.values():
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['POST'])
def login():
    data = request.form
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    if users.get(username) == password:
        token = f"token_{username}"
        sessions[username] = token
        return jsonify({"token": token}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/logout', methods=['POST'])
@authenticate
def logout():
    token = request.headers.get("X-OBSERVATORY-AUTH")
    user = next((u for u, t in sessions.items() if t == token), None)
    
    if user:
        del sessions[user]
        return "", 200
    return jsonify({"error": "Invalid session"}), 401

# Healthcheck endpoint
@app.route('/admin/healthcheck', methods=['GET'])
@authenticate
def healthcheck():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Enables fetching results as a dictionary
        
        cursor.execute("SELECT COUNT(*) AS n_stations FROM Toll")
        n_stations = cursor.fetchone()["n_stations"]
        
        cursor.execute("SELECT COUNT(*) AS n_tags FROM Tag")
        n_tags = cursor.fetchone()["n_tags"]
        
        cursor.execute("SELECT COUNT(*) AS n_passes FROM Pass")
        n_passes = cursor.fetchone()["n_passes"]
        
        conn.close()
        
        return jsonify({
            "status": "OK",
            "dbconnection": "active",
            "n_stations": n_stations,
            "n_tags": n_tags,
            "n_passes": n_passes
        }), 200
    except mysql.connector.Error as e:  # Handle DB Connection Issues
        return jsonify({
            "status": "failed",
            "dbconnection": "database connection error",
            "details": str(e)
        }), 401
    except Exception as e:  # Handle All Other Errors
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

@app.route('/admin/resetstations', methods=['POST'])
@authenticate
def reset_stations():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete all existing toll stations
        cursor.execute("DELETE FROM Toll")
        
        # Load new data from CSV file
        csv_file_path = '/path/to/tollstations2024.csv'  # Update this path
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            query = "INSERT INTO Toll (idToll, idOperator, Name, PM, Locality, Road, Latitude, Longitude, Email, Price_1, Price_2, Price_3, Price_4) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            for row in reader:
                cursor.execute(query, row)
        
        conn.commit()
        conn.close()
        
        return jsonify({"status": "OK"}), 200
    except Exception as e:
        return jsonify({"status": "failed", "info": str(e)}), 500

@app.route('/admin/resetpasses', methods=['POST'])
@authenticate
def reset_passes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete all pass records and dependent data
        cursor.execute("DELETE FROM Pass")
        cursor.execute("DELETE FROM Tag")
        
        # Reset admin user
        cursor.execute("DELETE FROM Users")
        cursor.execute("INSERT INTO Users (username, password) VALUES (%s, %s)", ("admin", "freepasses4all"))
        
        conn.commit()
        conn.close()
        
        return jsonify({"status": "OK"}), 200
    except Exception as e:
        return jsonify({"status": "failed", "info": str(e)}), 500

# Add passes from CSV file
@app.route('/admin/addpasses', methods=['POST'])
@authenticate
def add_passes():
    if 'file' not in request.files:
        return jsonify({"status": "failed", "info": "No file provided"}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({"status": "failed", "info": "Invalid file format. Must be CSV."}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        reader = csv.reader(io.StringIO(file.stream.read().decode("utf-8")))
        
        headers = next(reader)  # Read header row
        expected_headers = ["passID", "timestamp", "stationID", "tagID", "passCharge"]
        if headers != expected_headers:
            return jsonify({"status": "failed", "info": "Invalid CSV headers"}), 400
        
        query = "INSERT INTO Pass (passID, timestamp, idToll, idTag, Charge) VALUES (%s, %s, %s, %s, %s)"
        
        for row in reader:
            cursor.execute(query, row)
        
        conn.commit()
        conn.close()
        
        return jsonify({"status": "OK"}), 200
    except Exception as e:
        return jsonify({"status": "failed", "info": str(e)}), 500 


        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# Get passes by toll station
@app.route('/tollStationPasses/<tollStationID>/<date_from>/<date_to>', methods=['GET'])
@authenticate
def toll_station_passes(tollStationID, date_from, date_to):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT p.passID, p.timestamp, p.idToll AS stationID, t.idOperator AS stationOperator,
               p.idTag, tg.idOperator AS tagProvider, p.passType, p.Charge AS passCharge
        FROM Pass p
        JOIN Toll t ON p.idToll = t.idToll
        JOIN Tag tg ON p.idTag = tg.idTag
        WHERE p.idToll = %s AND p.timestamp BETWEEN %s AND %s
        ORDER BY p.timestamp ASC
        """
        
        cursor.execute(query, (tollStationID, date_from, date_to))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return jsonify({"message": "No data found for the given period."}), 204
        
        passList = [{
            "passIndex": idx + 1,
            "passID": row["passID"],
            "stationID": row["stationID"],
            "stationOperator": row["stationOperator"],
            "timestamp": row["timestamp"],
            "tagID": row["idTag"],
            "tagProvider": row["tagProvider"],
            "passType": row["passType"],
            "passCharge": row["passCharge"]
        } for idx, row in enumerate(results)]
        
        response_data = {
            "tollStationID": tollStationID,
            "requestTimestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "periodFrom": date_from,
            "periodTo": date_to,
            "nPasses": len(passList),
            "passList": passList
        }
        
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# Get pass Analysis 
@app.route('/passAnalysis/<stationOpID>/<tagOpID>/<date_from>/<date_to>', methods=['GET'])
@authenticate
def pass_analysis(stationOpID, tagOpID, date_from, date_to):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT p.passID, p.timestamp, p.idToll AS stationID, p.idTag, p.Charge AS passCharge
        FROM Pass p
        JOIN Toll t ON p.idToll = t.idToll
        WHERE t.idOperator = %s AND p.idOperator = %s
        AND p.timestamp BETWEEN %s AND %s
        ORDER BY p.timestamp ASC
        """
        
        cursor.execute(query, (stationOpID, tagOpID, date_from, date_to))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return jsonify({"message": "No data found for the given period."}), 204
        
        passList = [{
            "passIndex": idx + 1,
            "passID": row["passID"],
            "stationID": row["stationID"],
            "timestamp": row["timestamp"],
            "tagID": row["idTag"],
            "passCharge": row["passCharge"]
        } for idx, row in enumerate(results)]
        
        response_data = {
            "stationOpID": stationOpID,
            "tagOpID": tagOpID,
            "requestTimestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "periodFrom": date_from,
            "periodTo": date_to,
            "nPasses": len(passList),
            "passList": passList
        }
        
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# Get passes cost
@app.route('/passesCost/<tollOpID>/<tagOpID>/<date_from>/<date_to>', methods=['GET'])
@authenticate
def passes_cost(tollOpID, tagOpID, date_from, date_to):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT COUNT(p.idPass) AS nPasses, SUM(p.Charge) AS passesCost
        FROM Pass p
        JOIN Toll t ON p.idToll = t.idToll
        JOIN Tag tg ON p.idTag = tg.idTag
        WHERE t.idOperator = %s AND tg.idOperator = %s
        AND p.timestamp BETWEEN %s AND %s
        """
        
        cursor.execute(query, (tollOpID, tagOpID, date_from, date_to))
        result = cursor.fetchone()
        conn.close()
        
        if not result or result["nPasses"] == 0:
            return jsonify({"message": "No data found for the given period."}), 204
        
        response_data = {
            "tollOpID": tollOpID,
            "tagOpID": tagOpID,
            "requestTimestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "periodFrom": date_from,
            "periodTo": date_to,
            "nPasses": result["nPasses"],
            "passesCost": result["passesCost"]
        }
        
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/chargesBy/<tollOpID>/<date_from>/<date_to>', methods=['GET'])
@authenticate
def get_charges_by(tollOpID, date_from, date_to):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT p.idOperator AS tollOpID, t.idOperator AS visitingOpID, 
               COUNT(p.idPass) AS nPasses, SUM(p.Charge) AS passesCost
        FROM Pass p
        JOIN Tag t ON p.idTag = t.idTag
        WHERE p.passType = 'visitor'
        AND p.idOperator = %s
        AND p.timestamp BETWEEN %s AND %s
        GROUP BY p.idOperator, t.idOperator
        """
        
        cursor.execute(query, (tollOpID, date_from, date_to))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return jsonify({"message": "No data found for the given period."}), 204
        
        vOpList = [{
            "visitingOpID": row["visitingOpID"],
            "nPasses": row["nPasses"],
            "passesCost": row["passesCost"]
        } for row in results]
        
        response_data = {
            "tollOpID": tollOpID,
            "requestTimestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "periodFrom": date_from,
            "periodTo": date_to,
            "vOpList": vOpList
        }
        
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
        
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9115, debug=True)

