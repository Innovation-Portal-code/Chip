#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/Chip

# Ensure uv and Python are available
uv --version
python --version || true

# Create venv if missing and install deps
if [ ! -d .venv ]; then
  uv venv .venv --python $(uv python list --default)
fi

source .venv/bin/activate

# Sync dependencies using uv (respect lockfile)
if [ -f uv.lock ]; then
  uv sync --frozen --all-extras
else
  uv sync --all-extras
fi

echo "Devcontainer setup complete."


