#!/bin/bash

echo "Testing CLI commands..."

# Login
python cli.py login --username admin --password freepasses4all

# Healthcheck
python cli.py healthcheck

# Reset passes
python cli.py resetpasses

# Reset stations
python cli.py resetstations

# Add passes (Ensure test.csv exists in the directory)
python cli.py addpasses --file "file=@\"C:\Users\iomak\MySQL\MySQL Server 8.0\Uploads\passes23.csv\""

# Toll station passes
python cli.py tollstationpasses --station NAO01 --from 20240101 --to 20240131 --format json

# Pass analysis
python cli.py passanalysis --stationop NAO --tagop EG --from 20240101 --to 20240131 --format json

# Pass cost
python cli.py passescost --stationop NAO --tagop EG --from 20240101 --to 20240131 --format json

# Charges by operator
python cli.py chargesby --opid NAO --from 20240101 --to 20240131 --format json

# Logout
python cli.py logout

echo "CLI tests completed."
