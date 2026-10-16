#!/usr/bin/env bash
# Tests the built container image (the artifact), not the Python code:
# does it follow the image rules, start, serve the API, report its version,
# and shut down cleanly? Used by CI; runs locally too (needs Docker, curl, jq).
#
# Usage: scripts/test-image.sh IMAGE EXPECTED_VERSION
set -euo pipefail

IMAGE=${1:?usage: test-image.sh IMAGE EXPECTED_VERSION}
EXPECTED_VERSION=${2:?usage: test-image.sh IMAGE EXPECTED_VERSION}
NAME=taskflow-image-test
PORT=9000                 # not the default 8000: proves the image honors $PORT
MAX_SIZE_MB=250
BASE="http://127.0.0.1:$PORT"
BODY=$(mktemp)

pass() { echo "ok   - $*"; }
fail() { echo "::error::$*"; exit 1; }

cleanup() {
  local status=$?
  if [ "$status" -ne 0 ]; then
    echo "--- container logs"
    docker logs "$NAME" 2>&1 || true
  fi
  docker rm -f "$NAME" > /dev/null 2>&1 || true
  rm -f "$BODY"
}
trap cleanup EXIT

# request METHOD PATH [JSON]: prints the HTTP status, saves the response body in $BODY
request() {
  curl -s -o "$BODY" -w '%{http_code}' -X "$1" "$BASE$2" \
    -H 'content-type: application/json' ${3:+--data "$3"}
}

# expect STATUS METHOD PATH [JSON]
expect() {
  local want=$1 got
  shift
  got=$(request "$@")
  [ "$got" = "$want" ] || fail "$1 $2 returned $got, expected $want"
}

# --- Image rules (inspected without starting the app) -----------------------
user=$(docker image inspect --format '{{.Config.User}}' "$IMAGE")
if [ -z "$user" ] || [ "$user" = root ] || [ "$user" = 0 ]; then
  fail "image runs as root (USER='$user')"
fi
pass "runs as non-root user '$user'"

size_mb=$(( $(docker image inspect --format '{{.Size}}' "$IMAGE") / 1024 / 1024 ))
if [ "$size_mb" -gt "$MAX_SIZE_MB" ]; then
  fail "image is ${size_mb} MB, budget is ${MAX_SIZE_MB} MB"
fi
pass "image size ${size_mb} MB (budget ${MAX_SIZE_MB} MB)"

if docker run --rm "$IMAGE" sh -c 'test -e tests || python -c "import pytest"' 2> /dev/null; then
  fail "test code or dev dependencies are inside the image"
fi
pass "no tests/ or dev dependencies in the image"

# --- The running container ----------------------------------------------------
docker run --detach --name "$NAME" --env PORT="$PORT" \
  --publish "127.0.0.1:$PORT:$PORT" "$IMAGE" > /dev/null

for _ in $(seq 30); do
  curl -fs "$BASE/health" > /dev/null && break
  sleep 1
done
expect 200 GET /health
pass "starts and answers /health on \$PORT=$PORT"

version=$(jq -r .version "$BODY")
[ "$version" = "$EXPECTED_VERSION" ] || fail "/health reports version '$version', expected '$EXPECTED_VERSION'"
pass "reports version $version"

expect 201 POST /api/todos '{"title": "image test"}'
id=$(jq -r .id "$BODY")
expect 200 GET "/api/todos/$id"
expect 200 PATCH "/api/todos/$id" '{"done": true}'
[ "$(jq -r .done "$BODY")" = true ] || fail "PATCH did not mark the to-do done"
expect 204 DELETE "/api/todos/$id"
expect 404 GET "/api/todos/$id"
pass "to-do API works end to end (create, read, update, delete)"

expect 200 GET /
grep -q Taskflow "$BODY" || fail "/ does not serve the web UI"
pass "serves the web UI"

start=$(date +%s)
docker stop --time 10 "$NAME" > /dev/null
took=$(( $(date +%s) - start ))
code=$(docker inspect --format '{{.State.ExitCode}}' "$NAME")
if [ "$took" -ge 10 ] || [ "$code" -ne 0 ]; then
  fail "did not stop cleanly on SIGTERM (exit code $code after ${took}s)"
fi
pass "stops cleanly on SIGTERM (${took}s)"
