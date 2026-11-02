$ErrorActionPreference = 'Stop'
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e '.[dev,mcp]'
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
memora init
Write-Host "`nMemora installed. Start the API with: memora serve"
