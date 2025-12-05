# BioMLStudio DevContainer Setup

This directory contains the VS Code Dev Container configuration for BioMLStudio, enabling reproducible, containerized development environments for all team members.

## Files

- **devcontainer.json** — VS Code dev container configuration (orchestration, extensions, port forwarding)
- **Dockerfile** — Custom dev container image with Python 3.10+, Node.js 18+, debugpy, Docker CLI, and dev tools
- **docker-compose.override.yml** — Optional compose override to mount workspace and set environment variables
- **post-create.sh** — Post-build bootstrap script that installs Python venv, pip deps, and Node modules

## Quick Start (VS Code)

### Option 1: GUI (Recommended)

1. Open the repo folder in VS Code: `File → Open Folder → C:\Users\Someshwar\biomlstudio`
2. Command Palette: `Dev Containers: Reopen in Container`
3. Wait for the container to build and boot (first build ~2-3 min)
4. Once ready, open an integrated terminal (`` Ctrl+` ``)

### Option 2: CLI (WSL/Linux)

```bash
cd /mnt/c/Users/Someshwar/biomlstudio
# If you have devcontainer CLI installed
devcontainer build --workspace-folder . --file .devcontainer/devcontainer.json
devcontainer up --workspace-folder .
# Or use VS Code command palette as Option 1
```

## What's Included

Inside the DevContainer:

- ✅ **Python 3.10+** with `venv` module
- ✅ **Node.js 18+** with npm
- ✅ **debugpy** — Python debugger for VS Code
- ✅ **eslint** (global) — Node linter
- ✅ **Docker CLI** — talk to host Docker daemon
- ✅ **VS Code Extensions** — Python, Pylance, Prettier, Docker
- ✅ **Post-create automation** — auto-installs venv, pip deps, npm modules

## Post-Create Bootstrap

When the container starts, `post-create.sh` automatically:

1. Creates `.venv` if missing
2. Installs pip (upgrade) and test dependencies from `ml_engine/tests/requirements-ci.txt`
3. Installs backend npm modules (`npm ci`)
4. Prints completion message: `[devcontainer] post-create complete`

Heavy packages (like `torch`) use `|| true` to continue even if installation fails (acceptable for dev environment).

## Port Forwarding

The devcontainer forwards these ports to your host machine:

- **4000** — Backend API (Express)
- **3000** — Frontend (nginx) — if running via docker-compose
- **5678** — Python debugger (debugpy)

### From Windows (PowerShell)

After container is running:

```powershell
curl http://localhost:4000    # Backend health check
curl http://localhost:3000    # Frontend (if available)
```

### From WSL/Linux

```bash
curl http://localhost:4000
```

## Debugging

### Python Debugging

1. Set a breakpoint in any Python file (e.g., `ml_engine/tests/test_smoke_training.py`)
2. Command Palette: `Debug: Select and Start Debugging`
3. Choose `ML Worker (Python)` or `ML Training Script`
4. Debugger will pause at breakpoints

### Node Debugging

1. Set a breakpoint in `backend/src/server.js`
2. Command Palette: `Debug: Select and Start Debugging`
3. Choose `Backend (Node)`
4. Server will start in debug mode

## Running Tests Inside Container

```bash
# In the integrated terminal (inside container)
source /workspace/.venv/bin/activate

# Run ML tests
pytest ml_engine/tests/ -v

# Run smoke training
python ml_engine/tools/smoke_train.py --epochs 1

# Run local CI pipeline
bash scripts/run_local_ci.sh
```

## Docker Access Inside Container

The container has Docker CLI installed and can access the host Docker daemon:

```bash
# Inside container terminal
docker ps
docker-compose ps
docker-compose logs backend
```

This enables running full docker-compose stacks from within the container.

## Troubleshooting

### Container fails to build

**Error:** `docker: not found` or permission denied

- **Solution:** Ensure Docker Desktop is running (Windows) or docker daemon is active (Linux/WSL)
- For WSL integration: `Settings → Resources → WSL integration` must be enabled in Docker Desktop

### Python packages not installing (heavy deps like torch)

**Error:** `pip install torch` fails inside post-create

- **Expected:** Post-create script uses `|| true` to continue on heavy package failures
- **Solution:** Inside container, manually run `pip install torch==<version>+cpu` with your target version
- Or access the Windows .venv and install there first

### Git inside container not working

**Error:** `git: command not found`

- Already installed in base image, but verify: `which git`
- Mount your SSH keys or configure git credentials: `git config --global ...`

### Ports not forwarding

**Error:** `curl http://localhost:4000` returns "connection refused"

- Ensure backend is running: `node /workspace/backend/src/server.js`
- Check forwarded ports in devcontainer.json: should include 4000, 3000, 5678
- VS Code title bar should show `[Dev Container]` if connected

## Rebuilding the DevContainer

If you update the Dockerfile or dependencies, rebuild:

```bash
# VS Code: Command Palette → Dev Containers: Rebuild Container
# CLI: devcontainer build --workspace-folder . --skip-cache
```

## Next Steps

1. Open in container (GUI or CLI)
2. Wait for post-create to finish (watch terminal for `[devcontainer] post-create complete`)
3. Activate venv: `source /workspace/.venv/bin/activate`
4. Run tests: `pytest ml_engine/tests/ -v`
5. Start backend: `node /workspace/backend/src/server.js`
6. Open debugger: Command Palette → `Debug: Select and Start Debugging`

## References

- [VS Code Dev Containers Docs](https://code.visualstudio.com/docs/devcontainers/containers)
- [Dev Container CLI](https://github.com/devcontainers/cli)
- [BioMLStudio Implementation Blueprint](./../../DEVCONTAINER.md)

---

**Status:** ✅ Ready for team development. All extensions, debuggers, and tools pre-configured.
