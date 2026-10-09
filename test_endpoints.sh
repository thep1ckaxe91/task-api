#!/usr/bin/env bash
set -e

PORT=5055
BASE="http://127.0.0.1:$PORT"

# Temp file for CRUD tests (removed in cleanup)
BODY_FILE=$(mktemp)
HDR_FILE=$(mktemp)

# Run flask app in background on an unused port
FLASK_APP=app.py .venv/bin/python -c "from app import app; app.run(port=$PORT)" &
APP_PID=$!

cleanup() {
  kill "$APP_PID" 2>/dev/null || true
  rm -f "$BODY_FILE" "$HDR_FILE"
}
trap cleanup EXIT

# Wait for server to boot
for _ in {1..10}; do
  if curl -s "$BASE/docs" > /dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

echo "Testing /openapi.json..."
OPENAPI_RES=$(curl -s -w "\n%{http_code}" "$BASE/openapi.json")
HTTP_CODE=$(echo "$OPENAPI_RES" | tail -n1)
BODY=$(echo "$OPENAPI_RES" | head -n -1)
if [ "$HTTP_CODE" -ne 200 ] || ! echo "$BODY" | grep -q "openapi"; then
  echo "FAIL: /openapi.json returned $HTTP_CODE: $BODY"
  exit 1
fi
echo "PASS: /openapi.json (200 OK)"

echo "Testing /docs..."
DOCS_RES=$(curl -s -w "\n%{http_code}" "$BASE/docs")
HTTP_CODE=$(echo "$DOCS_RES" | tail -n1)
BODY=$(echo "$DOCS_RES" | head -n -1)
if [ "$HTTP_CODE" -ne 200 ] || ! echo "$BODY" | grep -q "SwaggerUIBundle"; then
  echo "FAIL: /docs returned $HTTP_CODE"
  exit 1
fi
echo "PASS: /docs (200 OK)"

# -----------------------------------
# CRUD tests
# -----------------------------------
PASS=0
FAIL=0

# call METHOD PATH [JSON_BODY [CONTENT_TYPE]] -> sets STATUS, BODY
call() {
  local method=$1 path=$2 ctype=${4:-application/json}
  if [[ $# -ge 3 ]]; then
    STATUS=$(curl -s -o "$BODY_FILE" -D "$HDR_FILE" -w '%{http_code}' \
      -X "$method" -H "Content-Type: $ctype" --data "$3" "$BASE$path")
  else
    STATUS=$(curl -s -o "$BODY_FILE" -D "$HDR_FILE" -w '%{http_code}' -X "$method" "$BASE$path")
  fi
  BODY=$(PYTHONIOENCODING=utf-8 .venv/bin/python - "$BODY_FILE" <<'PY'
import json, sys
raw = open(sys.argv[1], encoding="utf-8", errors="replace").read()
try:
    print(json.dumps(json.loads(raw), ensure_ascii=False, separators=(",", ":")), end="")
except ValueError:
    print(raw, end="")
PY
)
}

pass() { printf '  PASS  %s\n' "$1"; PASS=$((PASS+1)); }
fail() { printf '  FAIL  %s\n        status=%s body=%s\n' "$1" "$STATUS" "$BODY"; FAIL=$((FAIL+1)); }

# check DESC WANT_STATUS [BODY_SUBSTRING...]
check() {
  local desc=$1 want=$2; shift 2
  local ok=1 sub
  [[ $STATUS == "$want" ]] || ok=0
  for sub in "$@"; do [[ $BODY == *"$sub"* ]] || ok=0; done
  (( ok )) && pass "$desc" || fail "$desc"
}
check_exact()  { [[ $STATUS == "$2" && $BODY == "$3" ]] && pass "$1" || fail "$1"; }
check_empty()  { [[ $STATUS == "$2" && -z $BODY ]] && pass "$1" || fail "$1"; }
check_header() { grep -qi "$2" "$HDR_FILE" && pass "$1" || fail "$1 (header '$2' missing)"; }

echo "== GET /tasks"
call GET /tasks
check_exact "empty list -> 200 []" 200 "[]"

echo "== POST /tasks"
call POST /tasks '{"title":"Write openapi.yaml","description":"Design 5 endpoint","completed":false}'
check "full payload -> 201" 201 '"id":1' '"title":"Write openapi.yaml"' '"completed":false'
check_header "Location header present" '^location: /tasks/1'

call POST /tasks '{"title":"Only title"}'
check "title only -> 201, defaults applied" 201 '"id":2' '"description":""' '"completed":false'

call POST /tasks '{"description":"no title"}'
check "missing title -> 400" 400 'title is required'

call POST /tasks '{"title":""}'
check "empty title -> 400" 400 'title must be a non-empty string'

call POST /tasks '{"title":"   "}'
check "blank title -> 400" 400 'title must be a non-empty string'

call POST /tasks '{"title":123}'
check "title wrong type -> 400" 400 'title must be a non-empty string'

call POST /tasks '{"title":"x","completed":"yes"}'
check "completed not bool -> 400" 400 'completed must be a boolean'

call POST /tasks '{"title":"x","completed":1}';
check "completed=1 (int) -> 400" 400 'completed must be a boolean'

call POST /tasks '{"title":"x","description":42}'
check "description wrong type -> 400" 400 'description must be a string'

call POST /tasks '{"title":"x","id":99}'
check "client-supplied id (readOnly) -> 400" 400 '"error"'

call POST /tasks '["title"]'
check "JSON array body -> 400" 400

call POST /tasks '{"title": '
check "malformed JSON -> 400" 400

call POST /tasks 'title=x' 'text/plain'
check "non-JSON content-type -> 400" 400
 
echo "== GET /tasks (after creates)"
call GET /tasks
check "list has 2 tasks" 200 '"id":1' '"id":2'
[[ $BODY != *'"id":3'* ]] && pass "rejected POSTs did not consume/store ids" || fail "rejected POSTs leaked into store"
 
echo "== GET /tasks/<id>"
call GET /tasks/1
check "existing -> 200" 200 '"id":1' '"title":"Write openapi.yaml"'

call GET /tasks/999
check "missing -> 404" 404 'task not found'

call GET /tasks/abc
check "non-integer id -> 404 JSON" 404 '"error"'
 
echo "== PATCH /tasks/<id>"
call PATCH /tasks/1 '{"completed":true}'
check "partial update -> 200, title untouched" 200 '"completed":true' '"title":"Write openapi.yaml"' '"description":"Design 5 endpoint"'

call PATCH /tasks/1 '{"title":"Ver 2","description":"Add example"}'
check "multi-field update -> 200" 200 '"title":"Ver 2"' '"description":"Add example"' '"completed":true'

call PATCH /tasks/1 '{}'
check "empty body -> 400" 400 'at least one field'

call PATCH /tasks/1 '{"title":""}'
check "empty title -> 400" 400 'title must be a non-empty string'

call PATCH /tasks/1 '{"title":"Broken","completed":"no"}'
check "mixed valid+invalid -> 400" 400 'completed must be a boolean'

call GET /tasks/1
check "...and NOTHING was applied" 200 '"title":"Ver 2"'

call PATCH /tasks/999 '{"completed":true}'
check "missing id -> 404" 404 'task not found'
 
echo "== DELETE /tasks/<id>"
call DELETE /tasks/1
check_empty "existing -> 204, empty body" 204

call DELETE /tasks/1
check "again -> 404" 404 'task not found'

call GET /tasks/1
check "gone from GET -> 404" 404

call POST /tasks '{"title":"after delete"}'
check "new id is not recycled (3, not 1)" 201 '"id":3'
 
echo "== misc"
call PUT /tasks/2 '{"title":"x"}'
check "unsupported method -> 405 JSON" 405 '"error"'

call GET /nope
check "unknown route -> 404 JSON" 404 '"error"'

echo
echo "CRUD: passed=$PASS failed=$FAIL"
if [ "$FAIL" -ne 0 ]; then
  echo "FAIL: $FAIL CRUD check(s) failed"
  exit 1
fi

echo "All tests passed successfully!"
