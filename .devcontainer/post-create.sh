#!/usr/bin/env bash
set -e
echo "[devcontainer] post-create start"

# ensure workspace path
cd /workspace || exit 1

# Create Python venv if missing and install fast dev/test deps
if [ ! -d "/workspace/.venv" ]; then
  python3 -m venv /workspace/.venv
fi
source /workspace/.venv/bin/activate

pip install --upgrade pip
# Install test deps (best-effort; continue even if heavy packages fail)
pip install -r /workspace/ml_engine/tests/requirements-ci.txt || true

# Install backend npm deps as non-root user (no-audit for speed)
if [ -f /workspace/backend/package.json ]; then
  (cd /workspace/backend && npm ci --no-audit --no-fund) || true
fi

echo "[devcontainer] post-create complete"
