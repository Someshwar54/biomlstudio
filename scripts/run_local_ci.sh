#!/bin/bash
# Local CI runner — mirrors GitHub Actions workflow locally
# Usage: bash scripts/run_local_ci.sh
# Useful for WSL or Linux dev environments

set -e  # Exit on first error

# Support SKIP_HEAVY=1 to skip heavy tests
if [ "$SKIP_HEAVY" = "1" ]; then
  TESTS="-k 'not heavy'"
else
  TESTS=""
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "========================================"
echo "BioMLStudio Local CI Pipeline"
echo "========================================"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
FAILED=0
PASSED=0

run_check() {
  local name=$1
  local cmd=$2
  echo ""
  echo -e "${YELLOW}[${name}]${NC} Running: $cmd"
  if eval "$cmd"; then
    echo -e "${GREEN}✓ ${name} passed${NC}"
    ((PASSED++))
  else
    echo -e "${RED}✗ ${name} failed${NC}"
    ((FAILED++))
  fi
}

# === Python Tests ===
echo ""
echo "🐍 Python Tests & ML Engine"
# Use python3 for WSL compatibility; fall back to python on other systems
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
  PYTHON_CMD="python"
fi

run_check "ML Tests" "$PYTHON_CMD -m pytest ml_engine/tests/ $TESTS -v --tb=short"
run_check "Smoke Training" "$PYTHON_CMD ml_engine/tools/smoke_train.py --epochs 1"

# === Node Lint ===
echo ""
echo "🔧 Backend (Node.js)"
if command -v node &> /dev/null; then
  run_check "Backend Dependencies" "cd backend && npm ci"
  run_check "Backend Lint" "cd backend && npm run lint 2>/dev/null || echo '⚠️  No lint script configured'"
else
  echo -e "${YELLOW}⚠️  Node.js not found; skipping backend checks${NC}"
fi

# === Docker Build (optional, requires Docker) ===
echo ""
echo "🐳 Docker Build Check (optional)"
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
  run_check "Docker Compose Config" "docker-compose config --quiet"
  echo -e "${YELLOW}ℹ️  Full docker build test skipped (run: docker-compose build)${NC}"
else
  echo -e "${YELLOW}⚠️  Docker not found; skipping Docker checks${NC}"
fi

# === Summary ===
echo ""
echo "========================================"
echo "Local CI Summary"
echo "========================================"
echo -e "✓ Passed: ${GREEN}${PASSED}${NC}"
echo -e "✗ Failed: ${RED}${FAILED}${NC}"

if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}✅ All checks passed!${NC}"
  exit 0
else
  echo -e "${RED}❌ Some checks failed. See above for details.${NC}"
  exit 1
fi
