#!/usr/bin/env bash
set -e

PORT=5055

# Run flask app in background on an unused port
FLASK_APP=app.py .venv/bin/python -c "from app import app; app.run(port=$PORT)" &
APP_PID=$!

cleanup() {
  kill "$APP_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Wait for server to boot
for i in {1..10}; do
  if curl -s "http://127.0.0.1:$PORT/docs" > /dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

echo "Testing /openapi.json..."
OPENAPI_RES=$(curl -s -w "\n%{http_code}" "http://127.0.0.1:$PORT/openapi.json")
HTTP_CODE=$(echo "$OPENAPI_RES" | tail -n1)
BODY=$(echo "$OPENAPI_RES" | head -n -1)
if [ "$HTTP_CODE" -ne 200 ] || ! echo "$BODY" | grep -q "openapi"; then
  echo "FAIL: /openapi.json returned $HTTP_CODE: $BODY"
  exit 1
fi
echo "PASS: /openapi.json (200 OK)"

echo "Testing /docs..."
DOCS_RES=$(curl -s -w "\n%{http_code}" "http://127.0.0.1:$PORT/docs")
HTTP_CODE=$(echo "$DOCS_RES" | tail -n1)
BODY=$(echo "$DOCS_RES" | head -n -1)
if [ "$HTTP_CODE" -ne 200 ] || ! echo "$BODY" | grep -q "SwaggerUIBundle"; then
  echo "FAIL: /docs returned $HTTP_CODE"
  exit 1
fi
echo "PASS: /docs (200 OK)"

echo "Testing /tasks stub..."
TASKS_RES=$(curl -s -w "\n%{http_code}" "http://127.0.0.1:$PORT/tasks")
HTTP_CODE=$(echo "$TASKS_RES" | tail -n1)
if [ "$HTTP_CODE" -ne 501 ]; then
  echo "FAIL: /tasks stub expected 501, got $HTTP_CODE"
  exit 1
fi
echo "PASS: /tasks stub (501 Not Implemented)"

echo "All tests passed successfully!"
