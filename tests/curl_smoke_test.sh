#!/usr/bin/env bash
set -euo pipefail

PORT=${PORT:-5055}
BASE_URL="http://127.0.0.1:${PORT}"
VENV_PY=".venv/bin/python"
export PYTHONPATH="src:${PYTHONPATH:-}"

if [ ! -f "$VENV_PY" ]; then
    echo "ERROR: Virtual environment not found at .venv"
    exit 1
fi

echo "=================================================="
echo "Starting tasks-api Core Architecture Smoke Tests"
echo "Target Base URL: ${BASE_URL}"
echo "=================================================="

# 1. Generate test Bearer JWT token
TEST_TOKEN=$($VENV_PY -c "
from tasks_api.core.auth import generate_token
from tasks_api import create_app
app = create_app('testing')
with app.app_context():
    print(generate_token('test-curl-runner'))
")

# 2. Launch background test server
FLASK_ENV=testing OPENAPI_YAML_PATH="docs/openapi.yaml" $VENV_PY -c "
from tasks_api import create_app
app = create_app('testing')
app.run(host='127.0.0.1', port=${PORT}, debug=False)
" > /dev/null 2>&1 &
SERVER_PID=$!

cleanup() {
    echo "Stopping test server (PID: ${SERVER_PID})..."
    kill -9 "${SERVER_PID}" 2>/dev/null || true
}
trap cleanup EXIT

# 3. Wait for server to become responsive
MAX_RETRIES=20
COUNT=0
until curl -s -o /dev/null --max-time 1 "${BASE_URL}/health"; do
    sleep 0.2
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: Server failed to start within timeout."
        exit 1
    fi
done
echo "==> Server is up and running."

# 4. Test Cases execution
echo "Test 1: Healthcheck (GET /health) -> Expected 200 OK"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "${BASE_URL}/health")
if [ "$HTTP_STATUS" != "200" ]; then echo "FAIL: Expected 200, got $HTTP_STATUS"; exit 1; fi
echo "PASS (HTTP 200)"

echo "Test 2: OpenAPI JSON Specification (GET /openapi.json) -> Expected 200 OK"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "${BASE_URL}/openapi.json")
if [ "$HTTP_STATUS" != "200" ]; then echo "FAIL: Expected 200, got $HTTP_STATUS"; exit 1; fi
echo "PASS (HTTP 200)"

echo "Test 3: Swagger UI Interface (GET /docs) -> Expected 200 OK"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "${BASE_URL}/docs")
if [ "$HTTP_STATUS" != "200" ]; then echo "FAIL: Expected 200, got $HTTP_STATUS"; exit 1; fi
echo "PASS (HTTP 200)"

echo "Test 4: Unauthorized access without token (GET /tasks) -> Expected 401 Problem Details"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "${BASE_URL}/tasks")
if [ "$HTTP_STATUS" != "401" ]; then echo "FAIL: Expected 401, got $HTTP_STATUS"; exit 1; fi
echo "PASS (HTTP 401 RFC 7807)"

echo "Test 5: Authorized Task Creation (POST /tasks) -> Expected 201 Created"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 \
    -X POST "${BASE_URL}/tasks" \
    -H "Authorization: Bearer ${TEST_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"title": "Automated Smoke Test Task", "description": "Verification"}')
if [ "$HTTP_STATUS" != "201" ]; then echo "FAIL: Expected 201, got $HTTP_STATUS"; exit 1; fi
echo "PASS (HTTP 201)"

echo "Test 6: Authorized Task Retrieval (GET /tasks/task-stub-001) -> Expected 200 OK"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 \
    -X GET "${BASE_URL}/tasks/task-stub-001" \
    -H "Authorization: Bearer ${TEST_TOKEN}")
if [ "$HTTP_STATUS" != "200" ]; then echo "FAIL: Expected 200, got $HTTP_STATUS"; exit 1; fi
echo "PASS (HTTP 200)"

echo "Test 7: Authorized Task Partial Update (PATCH /tasks/task-stub-001) -> Expected 200 OK"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 \
    -X PATCH "${BASE_URL}/tasks/task-stub-001" \
    -H "Authorization: Bearer ${TEST_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"status": "completed"}')
if [ "$HTTP_STATUS" != "200" ]; then echo "FAIL: Expected 200, got $HTTP_STATUS"; exit 1; fi
echo "PASS (HTTP 200)"

echo "Test 8: Authorized Task Deletion (DELETE /tasks/task-stub-001) -> Expected 204 No Content"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 \
    -X DELETE "${BASE_URL}/tasks/task-stub-001" \
    -H "Authorization: Bearer ${TEST_TOKEN}")
if [ "$HTTP_STATUS" != "204" ]; then echo "FAIL: Expected 204, got $HTTP_STATUS"; exit 1; fi
echo "PASS (HTTP 204)"

echo "Test 9: Validation Error Missing Required Field (POST /tasks) -> Expected 422 Unprocessable Entity"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 \
    -X POST "${BASE_URL}/tasks" \
    -H "Authorization: Bearer ${TEST_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{}')
if [ "$HTTP_STATUS" != "422" ]; then echo "FAIL: Expected 422, got $HTTP_STATUS"; exit 1; fi
echo "PASS (HTTP 422 RFC 7807)"

echo "Test 10: Non-existent route (GET /invalid-endpoint) -> Expected 404 Problem Details"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "${BASE_URL}/invalid-endpoint")
if [ "$HTTP_STATUS" != "404" ]; then echo "FAIL: Expected 404, got $HTTP_STATUS"; exit 1; fi
echo "PASS (HTTP 404 RFC 7807)"

echo "=================================================="
echo "ALL SMOKE TESTS PASSED (10/10) SUCCESSFULLY!"
echo "=================================================="
exit 0
