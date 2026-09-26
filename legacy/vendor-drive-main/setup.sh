#!/bin/bash
# Vendor Drive — one-shot setup for Mac/Linux.
set -e
cd "$(dirname "$0")"
echo "=== Vendor Drive setup ==="

if ! command -v python3 &>/dev/null; then
  echo "Python 3 is required. Install it, then run this again."
  exit 1
fi

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

mkdir -p data uploads
if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo ">>> Created .env"
fi

echo ""
echo "Done. Two things left:"
echo "  1. Open .env and set SITE_PASSWORD (and paste your free Gemini + Tavily keys)."
echo "  2. Run:  source venv/bin/activate && python app.py"
echo "     Then open http://localhost:8000"
echo ""
