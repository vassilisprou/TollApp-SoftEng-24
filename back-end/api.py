from flask import Flask, request, jsonify, Response

import mysql.connector
from mysql.connector import Error
from collections import OrderedDict
import json
import csv
import io
import os
from functools import wraps
import pandas as pd
from datetime import datetime
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

users = {"admin": "freepasses4all"} 
sessions = {}  

if os.path.exists("session_store.json"):
    with open("session_store.json", "r") as f:
        sessions = json.load(f)


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
        host="localhost",       
        user="root",            
        password="01123581321Me!",            
        database="mydb"        
    )


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
    if not request.is_json: 
        data = request.form
    else:
        data = request.get_json()  
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    if users.get(username) == password:
        token = f"token_{username}"
        sessions[username] = token
        
        with open("session_store.json", "w") as f:
            json.dump(sessions, f)

        return jsonify({"token": token}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/logout', methods=['POST'])
@authenticate
def logout():
    token = request.headers.get("X-OBSERVATORY-AUTH")
    user = next((u for u, t in sessions.items() if t == token), None)
    
    if user:
        del sessions[user]
        return jsonify({"message": "Logout successful"}), 200  

    return jsonify({"error": "Invalid session"}), 401  




@app.route('/admin/healthcheck', methods=['GET'])
@authenticate
def healthcheck():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  
        
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
    except mysql.connector.Error as e: 
        return jsonify({
            "status": "failed",
            "dbconnection": "database connection error",
            "details": str(e)
        }), 401
    except Exception as e:  
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
        
       
        cursor.execute("DELETE FROM Toll")
        

        csv_file_path = 'C:/Users/iomak/MySQL/MySQL Server 8.0/Uploads/tollstations2024.csv'  # Update this path

        

       
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader) 

            query1 = "INSERT IGNORE INTO Operator (idOperator,name) VALUES (%s, %s)"
        
        
            for row in reader:
                cursor.execute(query1, (row[0], row[1]))

        conn.commit()

        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  
            query2 = """INSERT INTO Toll (idToll, idOperator, Name, PM, Locality, Road, Latitude, Longitude, Email, Price_1, Price_2, Price_3, Price_4) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            for row in reader:
                idOperator = row[0]
                idToll = row[2]  
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

               
                cursor.execute(query2, (idToll, idOperator, Name, PM, Locality, Road, Latitude, Longitude, Email, Price_1, Price_2, Price_3, Price_4))
        
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
        
        
        cursor.execute("DELETE FROM Pass")
        cursor.execute("DELETE FROM Tag")
        
     
        cursor.execute("DELETE FROM Users")
        cursor.execute("INSERT INTO Users (username, password) VALUES (%s, %s)", ("admin", "freepasses4all"))
        
        conn.commit()
        conn.close()
        
        return jsonify({"status": "OK"}), 200
    except Exception as e:
        return jsonify({"status": "failed", "info": str(e)}), 500


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
      
       
        file_content = file.stream.read().decode("utf-8-sig")
        reader = csv.reader(io.StringIO(file_content))

        headers = next(reader)
        expected_headers = ["timestamp", "tollID", "tagRef", "tagHomeID", "charge"]

        if headers != expected_headers:
          return jsonify({"status": "failed", "info": "Invalid CSV headers"}), 400
        
 
        tag_insert_query = "INSERT IGNORE INTO Tag (idTag, idOperator) VALUES (%s, %s)"
        
        for row in reader:
            cursor.execute(tag_insert_query, (row[2], row[3]))
     
        conn.commit()

  
        file.stream.seek(0)
        reader = csv.reader(io.StringIO(file_content))
        next(reader) 

    
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


@app.route('/tollStationPasses/<tollStationID>/<date_from>/<date_to>', methods=['GET'])
@authenticate
def toll_station_passes(tollStationID, date_from, date_to):
    try:
      
        start_date = datetime.strptime(date_from, '%Y%m%d')
        end_date = datetime.strptime(date_to, '%Y%m%d')

       
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)


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
        WHERE p.idToll = %s AND p.timestamp BETWEEN %s AND %s
        ORDER BY p.timestamp ASC
        """
 
        cursor.execute(query, (tollStationID, date_from_str, date_to_str))
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

  
    


@app.route('/passAnalysis/<stationOpID>/<tagOpID>/<date_from>/<date_to>', methods=['GET'])
@authenticate
def pass_analysis(stationOpID, tagOpID, date_from, date_to):
    try:
      
        start_date = datetime.strptime(date_from, '%Y%m%d')
        end_date = datetime.strptime(date_to, '%Y%m%d')

     
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)

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

        start_date = datetime.strptime(date_from, '%Y%m%d')
        end_date = datetime.strptime(date_to, '%Y%m%d')

    
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)

        date_from_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
        date_to_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT COUNT(p.idPass) AS nPasses,  SUM(ROUND(p.Charge,2)) AS passesCost
        FROM Pass p
        JOIN Toll t ON p.idToll = t.idToll
        JOIN Tag tg ON p.idTag = tg.idTag
        WHERE t.idOperator = %s AND tg.idOperator = %s
        AND p.timestamp BETWEEN %s AND %s
        """
     
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
    
        start_date = datetime.strptime(date_from, '%Y%m%d')
        end_date = datetime.strptime(date_to, '%Y%m%d')

   
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)


        date_from_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
        date_to_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

   
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

     
        cursor.execute(query, (tollOpID, date_from_str, date_to_str))
        results = cursor.fetchall()
        conn.close()

        if not results:
            return jsonify({"message": "No data found for the given period."}), 204

        vOpList = [{
            "visitingOpID": row["visitingOpID"],
            "nPasses": row["nPasses"],
            "passesCost":row["passesCost"], 
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

@app.route('/tolls', methods=['GET'])
@authenticate
def get_tolls():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT idToll, Name FROM Toll")
        tolls = cursor.fetchall()
        
        conn.close()
        return jsonify({"tolls": tolls}), 200
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route('/tags', methods=['GET'])
@authenticate
def get_tags():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT idTag, idOperator FROM Tag")
        tags = cursor.fetchall()
        
        conn.close()
        return jsonify({"tags": tags}), 200
    except Exception as e:
        return jsonify({"error": "Internal server error ", "details": str(e)}), 500



@app.route('/operatorPassesCount/<operatorID>', methods=['GET'])
@authenticate
def count_operator_passes(operatorID):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
  
        query = """
        SELECT COUNT(*) AS totalPasses
        FROM Pass p
        JOIN Toll t ON p.idToll = t.idToll
        WHERE t.idOperator = %s
        """
        
        cursor.execute(query, (operatorID,))
        result = cursor.fetchone()
        conn.close()

        if result and result["totalPasses"] is not None:
            return jsonify({"operatorID": operatorID, "totalPasses": result["totalPasses"]}), 200
        else:
            return jsonify({"operatorID": operatorID, "totalPasses": 0}), 200  

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route('/operatorDebts/<operatorID>', methods=['GET'])
@authenticate
def get_operator_debts(operatorID):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = f"""
        WITH operator_debts AS (
            SELECT
                t1.idOperator AS operatorA,
                tg1.idOperator AS operatorB,
                SUM(p1.Charge) AS debtA_to_B
            FROM Pass p1
            JOIN Toll t1 ON p1.idToll = t1.idToll
            JOIN Tag tg1 ON p1.idTag = tg1.idTag
            WHERE t1.idOperator = %s AND t1.idOperator != tg1.idOperator
            GROUP BY t1.idOperator, tg1.idOperator
        ),
        operator_credits AS (
            SELECT
                t2.idOperator AS operatorB,
                tg2.idOperator AS operatorA,
                SUM(p2.Charge) AS debtB_to_A
            FROM Pass p2
            JOIN Toll t2 ON p2.idToll = t2.idToll
            JOIN Tag tg2 ON p2.idTag = tg2.idTag
            WHERE tg2.idOperator = %s AND t2.idOperator != tg2.idOperator
            GROUP BY t2.idOperator, tg2.idOperator
        )
        SELECT
            COALESCE(od.operatorA, oc.operatorA) AS operatorA,
            COALESCE(od.operatorB, oc.operatorB) AS operatorB,
            COALESCE(od.debtA_to_B, 0) AS debtA_to_B,
            COALESCE(oc.debtB_to_A, 0) AS debtB_to_A,
            (COALESCE(od.debtA_to_B, 0) - COALESCE(oc.debtB_to_A, 0)) AS net_debt
        FROM operator_debts od
        LEFT JOIN operator_credits oc ON od.operatorB = oc.operatorB
        UNION ALL
        SELECT
            COALESCE(od.operatorA, oc.operatorA) AS operatorA,
            COALESCE(od.operatorB, oc.operatorB) AS operatorB,
            COALESCE(od.debtA_to_B, 0) AS debtA_to_B,
            COALESCE(oc.debtB_to_A, 0) AS debtB_to_A,
            (COALESCE(od.debtA_to_B, 0) - COALESCE(oc.debtB_to_A, 0)) AS net_debt
        FROM operator_debts od
        RIGHT JOIN operator_credits oc ON od.operatorB = oc.operatorB;
        """
        
        cursor.execute(query, (operatorID, operatorID))
        results = cursor.fetchall()
        conn.close()

        if not results:
            return jsonify({"message": "No debt data found for the given operator."}), 204
        
        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/operators', methods=['GET'])
@authenticate
def get_operators():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT idOperator, Name FROM Operator"
        cursor.execute(query)
        operators = cursor.fetchall()
        conn.close()

        if not operators:
            return jsonify({"message": "No operators found"}), 204
        
        return jsonify({"operators": operators}), 200

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/operator_passes_histogram', methods=['GET'])
@authenticate
def get_operator_passes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT t.idOperator AS operatorID, COUNT(p.idPass) AS totalPasses
        FROM Pass p
        JOIN Toll t ON p.idToll = t.idToll
        GROUP BY t.idOperator
        ORDER BY totalPasses DESC;
        """

        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        if not results:
            return jsonify({"message": "No data found"}), 204

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500



@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Bad Request", "details": "Invalid API endpoint"}), 400


        
if __name__ == '__main__':
    import ssl

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')

    app.run(host='0.0.0.0', port=9115, debug=True, ssl_context=context)



