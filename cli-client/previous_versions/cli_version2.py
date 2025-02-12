import requests
import argparse
import json
import csv
import sys
import os


BASE_URL = "http://127.0.0.1:9115"  # Update if hosted elsewhere
HEADERS = {"Content-Type": "application/json"}
SESSION_TOKEN = None  # Stores authentication token

# Utility function to make API requests
def api_request(method, endpoint, data=None, params=None,files=None,auth_required=False):
    global SESSION_TOKEN

    # Load the token from file if available
    if SESSION_TOKEN is None and os.path.exists("session_token.txt"):
        with open("session_token.txt", "r") as f:
            SESSION_TOKEN = f.read().strip()


    headers = HEADERS.copy()
    
    if auth_required and SESSION_TOKEN:
        headers["X-OBSERVATORY-AUTH"] = SESSION_TOKEN
    
   

    url = f"{BASE_URL}{endpoint}"
    if files is not None:
        response = requests.request(method, url, headers=headers, files=files)
    else:
        response = requests.request(method, url,headers=headers, json=data, params=params)
    
    
  
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 204:
        print("No content found.")
        sys.exit(0)
    else:
        print(f"Error: {response.status_code} - {response.text}")
        sys.exit(1)

# Function to handle authentication (Login)
def login(username, password):
    global SESSION_TOKEN
    response = api_request("POST", "/login", {"username": username, "password": password})
    SESSION_TOKEN = response.get("token")

    with open("session_token.txt", "w") as f:
        f.write(SESSION_TOKEN)

    print(f"Login successful. Token received: {SESSION_TOKEN}")

# Function to handle logout
def logout():
    api_request("POST", "/logout", auth_required=True)
    print("Logged out successfully.")

# Function to check health status
def healthcheck():
    response = api_request("GET", "/admin/healthcheck",auth_required=True)
    print(json.dumps(response, indent=4))

# Function to reset passes
def resetpasses():
    api_request("POST", "/admin/resetpasses", auth_required=True)
    print("Passes reset successfully.")

# Function to reset toll stations
def resetstations():
    api_request("POST", "/admin/resetstations", auth_required=True)
    print("Toll stations reset successfully.")


def addpasses(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found.")
        sys.exit(1)

    global SESSION_TOKEN
    if SESSION_TOKEN is None and os.path.exists("session_token.txt"):
        with open("session_token.txt", "r") as f:
            SESSION_TOKEN = f.read().strip()

    if not SESSION_TOKEN:
        print("❌ Error: No authentication token found. Please log in first.")
        sys.exit(1)

    # ✅ Open the file in binary mode
    with open(file_path, "rb") as file:
        files = {"file": (os.path.basename(file_path), file, "text/csv")}
        headers = {"X-OBSERVATORY-AUTH": SESSION_TOKEN}  # ✅ Correct Auth Header


        url = f"{BASE_URL}/admin/addpasses"
        response = requests.post(url, files=files, headers=headers)  # ✅ Use files parameter



        if response.status_code == 200:
            print(" Passes added successfully.")
        else:
            print(f"Error: {response.status_code} - {response.text}")
        sys.exit(1)





# Function to fetch toll station passes
def tollstationpasses(station, date_from, date_to, format="csv"):
    params = {"format": format}
    response = api_request("GET", f"/tollStationPasses/{station}/{date_from}/{date_to}", params=params, auth_required=True)
    print_output(response, format)

# Function to fetch pass analysis
def passanalysis(stationop, tagop, date_from, date_to, format="csv"):
    params = {"format": format}
    response = api_request("GET", f"/passAnalysis/{stationop}/{tagop}/{date_from}/{date_to}", params=params, auth_required=True)
    print_output(response, format)

# Function to fetch pass costs
def passescost(stationop, tagop, date_from, date_to, format="csv"):
    params = {"format": format}
    response = api_request("GET", f"/passesCost/{stationop}/{tagop}/{date_from}/{date_to}", params=params, auth_required=True)
    print_output(response, format)

# Function to fetch charges by operator
def chargesby(opid, date_from, date_to, format="csv"):
    params = {"format": format}
    response = api_request("GET", f"/chargesBy/{opid}/{date_from}/{date_to}", params=params, auth_required=True)
    print_output(response, format)

# Function to format and print output in JSON or CSV
def print_output(data, format):
    if format == "json":
        print(json.dumps(data, indent=4))
    else:  # Default is CSV
        keys = data.keys() if isinstance(data, dict) else data[0].keys()
        writer = csv.DictWriter(sys.stdout, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data if isinstance(data, list) else [data])

# Argument parser for CLI commands
def main():
    parser = argparse.ArgumentParser(description="CLI for Toll API")
    subparsers = parser.add_subparsers(dest="command")

    # Login
    login_parser = subparsers.add_parser("login")
    login_parser.add_argument("--username", required=True)
    login_parser.add_argument("--password", required=True)

    # Logout
    subparsers.add_parser("logout")

    # Healthcheck
    subparsers.add_parser("healthcheck")

    # Reset passes
    subparsers.add_parser("resetpasses")

    #Add passes
    addpasses_parser = subparsers.add_parser("addpasses")
    addpasses_parser.add_argument("--file", required=True, help="Path to the CSV file")

    # Reset stations
    subparsers.add_parser("resetstations")

    # Toll station passes
    toll_parser = subparsers.add_parser("tollstationpasses")
    toll_parser.add_argument("--station", required=True)
    toll_parser.add_argument("--from", dest="date_from", required=True)
    toll_parser.add_argument("--to", dest="date_to", required=True)
    toll_parser.add_argument("--format", choices=["csv", "json"], default="csv")

    # Pass analysis
    pass_parser = subparsers.add_parser("passanalysis")
    pass_parser.add_argument("--stationop", required=True)
    pass_parser.add_argument("--tagop", required=True)
    pass_parser.add_argument("--from", dest="date_from", required=True)
    pass_parser.add_argument("--to", dest="date_to", required=True)
    pass_parser.add_argument("--format", choices=["csv", "json"], default="csv")

    # Pass cost
    cost_parser = subparsers.add_parser("passescost")
    cost_parser.add_argument("--stationop", required=True)
    cost_parser.add_argument("--tagop", required=True)
    cost_parser.add_argument("--from", dest="date_from", required=True)
    cost_parser.add_argument("--to", dest="date_to", required=True)
    cost_parser.add_argument("--format", choices=["csv", "json"], default="csv")

    # Charges by operator
    charges_parser = subparsers.add_parser("chargesby")
    charges_parser.add_argument("--opid", required=True)
    charges_parser.add_argument("--from", dest="date_from", required=True)
    charges_parser.add_argument("--to", dest="date_to", required=True)
    charges_parser.add_argument("--format", choices=["csv", "json"], default="csv")

    args = parser.parse_args()

    if args.command == "login":
        login(args.username, args.password)
    elif args.command == "logout":
        logout()
    elif args.command == "healthcheck":
        healthcheck()
    elif args.command == "resetpasses":
        resetpasses()
    elif args.command == "addpasses":  
        addpasses(args.file)
    elif args.command == "resetstations":
        resetstations()
    elif args.command == "tollstationpasses":
        tollstationpasses(args.station, args.date_from, args.date_to, args.format)
    elif args.command == "passanalysis":
        passanalysis(args.stationop, args.tagop, args.date_from, args.date_to, args.format)
    elif args.command == "passescost":
        passescost(args.stationop, args.tagop, args.date_from, args.date_to, args.format)
    elif args.command == "chargesby":
        chargesby(args.opid, args.date_from, args.date_to, args.format)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
