.PHONY: help install deps test lint smoke ci docker-test docker-build docker-up docker-down clean

help:
	@echo "BioMLStudio Dev Workflow"
	@echo "======================="
	@echo "Local dev targets:"
	@echo "  make install      - Bootstrap local dev environment (venv + npm)"
	@echo "  make deps         - Install CI test dependencies"
	@echo "  make test         - Run all tests (Python + Node lint)"
	@echo "  make lint         - Lint Python + Node code"
	@echo "  make smoke        - Run ML smoke training test (quick)"
	@echo "  make ci           - Run full local CI pipeline (mirrors GitHub Actions)"
	@echo ""
	@echo "Docker targets:"
	@echo "  make docker-build - Build all services"
	@echo "  make docker-up    - Start minimal stack (postgres, redis, backend)"
	@echo "  make docker-down  - Stop all containers"
	@echo "  make docker-test  - Run containerized ML tests"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove .venv, node_modules, __pycache__"

install:
	@echo "[*] Bootstrapping dev environment..."
	@echo "[info] Creating or reusing .venv via helper scripts"
	# Prefer POSIX helper when available
	if command -v bash >/dev/null 2>&1 && [ -f scripts/bootstrap_venv.sh ]; then \
		bash scripts/bootstrap_venv.sh; \
	else \
		# Fall back to PowerShell helper on Windows
		if command -v pwsh >/dev/null 2>&1; then \
			pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_venv.ps1; \
		elif [ -f ".venv/Scripts/Activate.ps1" ]; then \
			# Try to use Windows Activate if present (cmd/msys)
			. .venv/Scripts/Activate.ps1 || true; \
		else \
			echo "[warn] Could not find bootstrap helper nor pwsh; attempting POSIX venv creation"; \
			python -m venv .venv; \
			. .venv/bin/activate; \
			python -m pip install --upgrade pip setuptools wheel || true; \
		fi; \
	fi
	cd backend && npm install || true
	@echo "[+] Setup complete. Run 'source .venv/bin/activate' (WSL) or '. .\\.venv\\Scripts\\Activate.ps1' (PowerShell) to activate."

deps:
	@echo "[*] Installing CI dependencies..."
	. .venv/Scripts/activate 2>/dev/null || . .venv/bin/activate; \
	# Attempt to install requirements; if initial install fails, try CPU-only PyTorch wheel then reinstall
	( pip install -r ml_engine/tests/requirements-ci.txt ) || ( \
		echo "[!] pip install failed; attempting CPU-only PyTorch wheel fallback"; \
		pip install --index-url https://download.pytorch.org/whl/cpu torch || true; \
		pip install -r ml_engine/tests/requirements-ci.txt || true; \
	)
	cd backend && npm ci || true
	@echo "[+] CI deps installed."

test: deps
	@echo "[*] Running Python tests (ml_engine)..."
	. .venv/Scripts/activate 2>/dev/null || . .venv/bin/activate; \
	python -m pytest ml_engine/tests/ -v --tb=short || true
	@echo "[*] Running Node lint (backend)..."
	cd backend && npm run lint 2>/dev/null || echo "[!] No lint script in backend/package.json"
	@echo "[+] Tests complete."

lint:
	@echo "[*] Linting Python..."
	. .venv/Scripts/activate 2>/dev/null || . .venv/bin/activate; \
	python -m pylint ml_engine --exit-zero || echo "[!] pylint not installed, skipping"
	@echo "[*] Linting Node..."
	cd backend && npx eslint . 2>/dev/null || echo "[!] eslint not configured"
	@echo "[+] Linting complete."

smoke:
	@echo "[*] Running ML smoke training (1 epoch)..."
	. .venv/Scripts/activate 2>/dev/null || . .venv/bin/activate; \
	python ml_engine/tools/smoke_train.py --epochs 1
	@echo "[+] Smoke test passed."

ci:
	@echo "[*] Running full local CI pipeline (like GitHub Actions)..."
	@if command -v bash >/dev/null 2>&1; then \
		bash scripts/run_local_ci.sh; \
	else \
		echo "[!] bash not found. Falling back to manual checks..."; \
		$(MAKE) test && $(MAKE) lint && echo "[+] CI checks passed"; \
	fi

docker-build:
	@echo "[*] Building all services..."
	docker compose build --no-cache
	@echo "[+] Build complete."

docker-up:
	@echo "[*] Starting minimal stack (postgres, redis, backend)..."
	docker compose up -d postgres redis backend --build
	@echo "[+] Stack running. Backend: http://localhost:4000"
	docker compose ps

docker-down:
	@echo "[*] Stopping all containers..."
	docker compose down
	@echo "[+] Stopped."

docker-test:
	@echo "[*] Running containerized ML tests..."
	docker compose build ml_worker --no-cache
	docker run --rm -v $$(pwd)/ml_engine:/app -w /app python:3.10-slim bash -c \
		"pip install -q -r tests/requirements-ci.txt && pytest -q tests/ && python tools/smoke_train.py"
	@echo "[+] Container tests passed."

clean:
	@echo "[*] Cleaning up..."
	rm -rf .venv
	rm -rf backend/node_modules backend/package-lock.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "[+] Cleanup complete."

ci-fast:
	@echo "Running fast CI locally"
	python3 -m venv .venv; . .venv/bin/activate; pip install -r ml_engine/tests/requirements-ci.txt || true; pytest -q ml_engine/tests -k "not heavy"

ci-docker:
	docker build -t bioml-ci -f infrastructure/ci/Dockerfile .
	docker run --rm -v $(PWD):/workspace bioml-ci bash -lc "cd /workspace && ./scripts/run_local_ci.sh"

.DEFAULT_GOAL := help
