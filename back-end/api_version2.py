from flask import Flask, request, jsonify, Response

import mysql.connector
from mysql.connector import Error
from collections import OrderedDict

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
        password="01123581321Me!",            # Your MySQL password
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
        csv_file_path = 'C:/Users/iomak/MySQL/MySQL Server 8.0/Uploads/tollstations2024.csv'  # Update this path
        query = """INSERT INTO Toll (idToll, idOperator, Name, PM, Locality, Road, Latitude, Longitude, Email, Price_1, Price_2, Price_3, Price_4) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                idOperator = row[0]
                idToll = row[2]  # @dummy (row[1]) is ignored
                Name = row[3]
                PM = row[4]
                Locality = row[5]
                Road = row[6]
                Latitude = row[7]
                Longitude = row[8]
                Email = row[9]
                Price_1 = row[10]
                Price_2 = row[11]
                Price_3 = row[12]
                Price_4 = row[13]

                 # Execute the query
                cursor.execute(query, (idToll, idOperator, Name, PM, Locality, Road, Latitude, Longitude, Email, Price_1, Price_2, Price_3, Price_4))
        
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
      
        # Read the CSV with utf-8-sig encoding to remove BOM
        file_content = file.stream.read().decode("utf-8-sig")
        reader = csv.reader(io.StringIO(file_content))

        headers = next(reader)  # Read header row
        expected_headers = ["timestamp", "tollID", "tagRef", "tagHomeID", "charge"]

        if headers != expected_headers:
          return jsonify({"status": "failed", "info": "Invalid CSV headers"}), 400
        
         # Query for inserting missing idTag into the Tag table
        tag_insert_query = "INSERT IGNORE INTO Tag (idTag, idOperator) VALUES (%s, %s)"
        
        # Insert missing tags first
        for row in reader:
            cursor.execute(tag_insert_query, (row[2], row[3]))
        
        # Commit the tag insertions
        conn.commit()

        # Now reset the cursor position to read the file again (since it was consumed above)
        file.stream.seek(0)
        reader = csv.reader(io.StringIO(file_content))
        next(reader)  # Skip the header again

        # Insert the Pass records
        pass_query = "INSERT INTO Pass (timestamp, idToll, idTag, idOperator, Charge) VALUES (%s, %s, %s, %s, %s)"
        
        for row in reader:
            cursor.execute(pass_query, (row[0], row[1], row[2], row[3], row[4]))
        
        update_pass_type_query = """
        UPDATE mydb.Pass 
        JOIN mydb.Toll ON mydb.Pass.idToll = mydb.Toll.idToll 
        SET mydb.Pass.passType =
            CASE 
                WHEN mydb.Pass.idOperator = mydb.Toll.idOperator THEN 'home'
                ELSE 'visitor'
            END;
        """
        cursor.execute(update_pass_type_query)
        
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
        # Parse the dates from 'YYYYMMDD' format
        start_date = datetime.strptime(date_from, '%Y%m%d')
        end_date = datetime.strptime(date_to, '%Y%m%d')

        # Adjust the start and end times to start and end of day for 'YYYY-MM-DD' format
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)

        # Convert the datetime objects to string for SQL query in 'YYYY-MM-DD HH:MM:SS' format
        date_from_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
        date_to_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Create database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query to fetch passes within the given time range
        query = """
        SELECT p.idPass AS passID, p.timestamp, p.idToll AS stationID, t.idOperator AS stationOperator,
               p.idTag, tg.idOperator AS tagProvider, p.passType, p.Charge AS passCharge
        FROM Pass p
        JOIN Toll t ON p.idToll = t.idToll
        JOIN Tag tg ON p.idTag = tg.idTag
        WHERE p.idToll = %s AND p.timestamp BETWEEN %s AND %s
        ORDER BY p.timestamp ASC
        """
        
        # Execute the query
        cursor.execute(query, (tollStationID, date_from_str, date_to_str))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return jsonify({"message": "No data found for the given period."}), 204
        
        # Format the results into a structured response
        passList = [{
            "passIndex": idx + 1,
            "passID": row["passID"],
            "timestamp": row["timestamp"],
            "tagID": row["idTag"],
            "tagProvider": row["tagProvider"],
            "passType": row["passType"],
            "passCharge": row["passCharge"]
        } for idx, row in enumerate(results)]
        passList = [OrderedDict([
            ("passIndex", idx + 1),
            ("passID", row["passID"]),
            ("stationID", row["stationID"]),
            ("stationOperator", row["stationOperator"]),
            ("timestamp", row["timestamp"]),
            ("tagID", row["idTag"]),
            ("tagProvider", row["tagProvider"]),
            ("passType", row["passType"]),
            ("passCharge", row["passCharge"])
        ]) for idx, row in enumerate(results)]

        response_data = [OrderedDict([
            ("stationID", tollStationID),
            ("stationOperator", results[0]["stationOperator"]),
            ("requestTimestamp", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')),
            ("periodFrom", date_from),
            ("periodTo", date_to),
            ("nPasses", len(passList)),
            ( "passList", passList)])]
      
        
        return jsonify(response_data), 200
    
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

  
    

# Get pass Analysis 
@app.route('/passAnalysis/<stationOpID>/<tagOpID>/<date_from>/<date_to>', methods=['GET'])
@authenticate
def pass_analysis(stationOpID, tagOpID, date_from, date_to):
    try:
        # Parse the dates from 'YYYYMMDD' format
        start_date = datetime.strptime(date_from, '%Y%m%d')
        end_date = datetime.strptime(date_to, '%Y%m%d')

        # Adjust the start and end times to start and end of day for 'YYYY-MM-DD' format
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)

        # Convert the datetime objects to string for SQL query in 'YYYY-MM-DD HH:MM:SS' format
        date_from_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
        date_to_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT p.idPass AS passID, p.timestamp, p.idToll AS stationID, t.idOperator AS stationOperator,
               p.idTag, tg.idOperator AS tagProvider, p.passType, p.Charge AS passCharge
        FROM Pass p
        JOIN Toll t ON p.idToll = t.idToll
        JOIN Tag tg ON p.idTag = tg.idTag
        WHERE t.idOperator = %s AND tg.idOperator = %s AND p.timestamp BETWEEN %s AND %s
        ORDER BY p.timestamp ASC
        """
        
        cursor.execute(query, (stationOpID, tagOpID, date_from, date_to))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return jsonify({"message": "No data found for the given period."}), 204
        

        passList = [OrderedDict([
            ("passIndex", idx + 1),
            ("passID", row["passID"]),
            ("stationID", row["stationID"]),
            ("stationOperator", row["stationOperator"]),
            ("timestamp", row["timestamp"]),
            ("tagID", row["idTag"]),
            ("tagProvider", row["tagProvider"]),
            ("passType", row["passType"]),
            ("passCharge", row["passCharge"])
        ]) for idx, row in enumerate(results)]

        response_data = [OrderedDict([
            ("stationOpID", stationOpID),
            ("tagOpID", tagOpID),
            ("requestTimestamp", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')),
            ("periodFrom", date_from),
            ("periodTo", date_to),
            ("nPasses", len(passList)),
            ( "passList", passList)])]
            
            
        
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500




@app.route('/passesCost/<tollOpID>/<tagOpID>/<date_from>/<date_to>', methods=['GET'])
@authenticate
def passes_cost(tollOpID, tagOpID, date_from, date_to):
    try:
        # Parse the dates from 'YYYYMMDD' format
        start_date = datetime.strptime(date_from, '%Y%m%d')
        end_date = datetime.strptime(date_to, '%Y%m%d')

        # Adjust the start and end times to start and end of day for 'YYYY-MM-DD' format
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)

        # Convert the datetime objects to string for SQL query in 'YYYY-MM-DD HH:MM:SS' format
        date_from_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
        date_to_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT COUNT(p.idPass) AS nPasses, SUM(ROUND(p.Charge),2) AS passesCost
        FROM Pass p
        JOIN Toll t ON p.idToll = t.idToll
        JOIN Tag tg ON p.idTag = tg.idTag
        WHERE t.idOperator = %s AND tg.idOperator = %s
        AND p.timestamp BETWEEN %s AND %s
        """
        
        # Use the corrected date strings (date_from_str and date_to_str) in the query
        cursor.execute(query, (tollOpID, tagOpID, date_from_str, date_to_str))
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
        # Parse the dates from 'YYYYMMDD' format
        start_date = datetime.strptime(date_from, '%Y%m%d')
        end_date = datetime.strptime(date_to, '%Y%m%d')

        # Adjust the start and end times to start and end of day for 'YYYY-MM-DD' format
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)

        # Convert the datetime objects to string for SQL query in 'YYYY-MM-DD HH:MM:SS' format
        date_from_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
        date_to_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Updated query
        query = """
        SELECT p.idOperator AS visitingOpID,
               COUNT(p.idPass) AS nPasses, SUM(ROUND(p.Charge,2)) AS passesCost
        FROM Pass p
        JOIN Toll toll ON p.idToll = toll.idToll
        JOIN Tag tg ON p.idTag = tg.idTag
        WHERE toll.idOperator = %s  -- tollOpID
        AND p.passType = 'visitor'
        AND p.timestamp BETWEEN %s AND %s
        GROUP BY p.idOperator, tg.idOperator
        """

        # Execute the query using the formatted date range and tollOpID
        cursor.execute(query, (tollOpID, date_from_str, date_to_str))
        results = cursor.fetchall()
        conn.close()

        if not results:
            return jsonify({"message": "No data found for the given period."}), 204

        # Construct the visiting operators list
        vOpList = [{
            "visitingOpID": row["visitingOpID"],
            "nPasses": row["nPasses"],
            "passesCost":row["passesCost"], 
        } for row in results]

        # Prepare the response data
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