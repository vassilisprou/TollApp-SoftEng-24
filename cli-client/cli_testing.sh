#!/bin/bash

echo "Logging in..."
curl -X POST http://127.0.0.1:9115/login -d "username=admin&password=freepasses4all" -o login_response.json

TOKEN=$(jq -r '.token' login_response.json)

echo "Checking health status..."
curl -X GET http://127.0.0.1:9115/admin/healthcheck -H "X-OBSERVATORY-AUTH: $TOKEN"

echo "Resetting stations..."
curl -X POST http://127.0.0.1:9115/admin/resetstations -H "X-OBSERVATORY-AUTH: $TOKEN"

echo "Resetting passes..."
curl -X POST http://127.0.0.1:9115/admin/resetpasses -H "X-OBSERVATORY-AUTH: $TOKEN"

echo "Adding passes from CSV..."
curl -X POST http://127.0.0.1:9115/admin/addpasses -H "X-OBSERVATORY-AUTH: $TOKEN" -F "file=@\"C:\Users\iomak\MySQL\MySQL Server 8.0\Uploads\passes23.csv\""

echo "Getting passes cost..."
curl -X GET "http://127.0.0.1:9115/passesCost/NAO/EG/20220101/20220131" -H "X-OBSERVATORY-AUTH: $TOKEN"

echo "Getting charges by operator..."
curl -X GET "http://127.0.0.1:9115/chargesBy/NAO/20220101/20220131" -H "X-OBSERVATORY-AUTH: $TOKEN"

echo "Tests completed."
