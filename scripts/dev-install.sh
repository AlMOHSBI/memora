#!/usr/bin/env sh
set -eu
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,mcp]'
cp -n .env.example .env 2>/dev/null || true
memora init
printf '\nMemora installed. Start the API with: memora serve\n'
