#!/bin/bash
# Quick deployment verification script for Railway

echo "=========================================="
echo "Railway Deployment Verification"
echo "=========================================="
echo ""

# Get Railway app URL (replace with your actual URL)
RAILWAY_URL="${RAILWAY_URL:-your-app.railway.app}"

echo "Testing: https://${RAILWAY_URL}"
echo ""

# Test 1: Health check
echo "[TEST 1] Health Check..."
curl -s "https://${RAILWAY_URL}/health" | jq '.' || echo "Failed"
echo ""

# Test 2: Convert endpoint
echo "[TEST 2] Convert Endpoint..."
RESPONSE=$(curl -s -X POST "https://${RAILWAY_URL}/convert" \
  -H "Content-Type: application/json" \
  -d '{"youtube_url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","duration":30}')

echo "$RESPONSE" | jq '.'
JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
echo ""

if [ "$JOB_ID" != "null" ] && [ -n "$JOB_ID" ]; then
    echo "[TEST 3] Status Endpoint (Job ID: $JOB_ID)..."
    sleep 3
    curl -s "https://${RAILWAY_URL}/status/${JOB_ID}" | jq '.'
    echo ""

    echo "[TEST 4] Monitor job progress..."
    for i in {1..10}; do
        STATUS=$(curl -s "https://${RAILWAY_URL}/status/${JOB_ID}" | jq -r '.status')
        PROGRESS=$(curl -s "https://${RAILWAY_URL}/status/${JOB_ID}" | jq -r '.progress')
        MESSAGE=$(curl -s "https://${RAILWAY_URL}/status/${JOB_ID}" | jq -r '.message')

        echo "[${i}/10] Status: $STATUS | Progress: $PROGRESS% | $MESSAGE"

        if [ "$STATUS" = "completed" ] || [ "$STATUS" = "error" ]; then
            break
        fi

        sleep 5
    done
else
    echo "No job_id returned. Check if /convert endpoint is working."
fi

echo ""
echo "=========================================="
echo "Verification Complete"
echo "=========================================="
