#!/bin/bash
# Quick Deployment Verification for Railway
# Run this after Railway finishes deploying (2-3 minutes)

# Set your Railway URL here
RAILWAY_URL="${1:-your-app.railway.app}"

echo "=========================================="
echo "Railway Deployment Verification"
echo "=========================================="
echo ""
echo "Testing: https://${RAILWAY_URL}"
echo ""

# Test 1: Health Check
echo "[1/4] Health Check..."
curl -s "https://${RAILWAY_URL}/health" | python -m json.tool 2>/dev/null || echo "FAIL"
echo ""

# Test 2: Convert Endpoint
echo "[2/4] Starting conversion job..."
RESPONSE=$(curl -s -X POST "https://${RAILWAY_URL}/convert" \
  -H "Content-Type: application/json" \
  -d '{"youtube_url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","duration":30}')

echo "$RESPONSE" | python -m json.tool 2>/dev/null
JOB_ID=$(echo "$RESPONSE" | python -c "import sys,json; print(json.load(sys.stdin).get('job_id',''))" 2>/dev/null)
echo ""

if [ -n "$JOB_ID" ]; then
    echo "[3/4] Checking job status (Job ID: $JOB_ID)..."
    sleep 5
    curl -s "https://${RAILWAY_URL}/status/${JOB_ID}" | python -m json.tool 2>/dev/null
    echo ""

    echo "[4/4] Testing invalid job ID (should return JSON, not 404)..."
    curl -s "https://${RAILWAY_URL}/status/invalid-test-id" | python -m json.tool 2>/dev/null
    echo ""
else
    echo "[SKIP] No job_id returned"
fi

echo ""
echo "=========================================="
echo "Verification Complete"
echo "=========================================="
echo ""
echo "Expected results:"
echo "✓ Health check returns {\"status\": \"healthy\"}"
echo "✓ Convert returns job_id"
echo "✓ Status returns JSON (never 404)"
echo ""
echo "Check Railway logs: railway logs --tail"
