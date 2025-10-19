#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting test environment..."
docker-compose -f docker-compose.test.yml up -d

echo "⏳ Waiting for services to be ready..."

wait_for_port() {
  local host="$1"; local port="$2"; local retries=30; local i=0
  until (echo > /dev/tcp/${host}/${port}) >/dev/null 2>&1; do
    i=$((i+1))
    if [ "$i" -ge "$retries" ]; then
      echo "✗ Timeout waiting for ${host}:${port}"
      return 1
    fi
    sleep 1
  done
  return 0
}

# Wait for mapped ports on localhost (compose maps ports)
wait_for_port "localhost" 5432
wait_for_port "localhost" 27017
wait_for_port "localhost" 6379

echo "🧪 Running pytest with coverage inside test-runner..."
docker-compose -f docker-compose.test.yml run --rm test-runner \
  pytest tests/ --cov=src --cov-report=html --cov-report=term -v

EXIT_CODE=$?

echo "📊 Coverage report generated in htmlcov/index.html"

echo "🧹 Tearing down test environment..."
docker-compose -f docker-compose.test.yml down -v

exit ${EXIT_CODE}
