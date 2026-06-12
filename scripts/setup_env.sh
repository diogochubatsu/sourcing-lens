#!/bin/bash
# ArbitLens Environment Setup Script
# Sets up Python venv and installs all dependencies
# Usage: bash /mnt/ssd/arbitlens/scripts/setup_env.sh

set -euo pipefail

PROJECT_ROOT="/mnt/ssd/arbitlens"
VENV_DIR="$PROJECT_ROOT/.venv"

echo "=== ArbitLens Environment Setup ==="
echo "Project root: $PROJECT_ROOT"
echo "Venv: $VENV_DIR"
echo ""

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python venv..."
    python3.11 -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"
echo "Python: $(python --version)"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Core ML dependencies (SigLIP2)
echo ""
echo "=== Installing SigLIP2 + dependencies ==="
pip install transformers torch pillow

# Verify SigLIP2
python -c "
from transformers import AutoModel, AutoProcessor
from PIL import Image
import torch
model = AutoModel.from_pretrained('google/siglip2-base-patch16-224')
processor = AutoProcessor.from_pretrained('google/siglip2-base-patch16-224')
img = Image.new('RGB', (224, 224), color='red')
inputs = processor(images=img, return_tensors='pt')
with torch.no_grad():
    out = model.get_image_features(**inputs)
    emb = out.pooler_output if hasattr(out, 'pooler_output') else out
print('SigLIP2 OK - embedding shape:', emb.shape)
"

# Crawl4AI
echo ""
echo "=== Installing Crawl4AI ==="
pip install crawl4ai
crawl4ai-setup  # Install Playwright browsers

python -c "from crawl4ai import AsyncWebCrawler; print('Crawl4AI OK')"

# browser-use
echo ""
echo "=== Installing browser-use ==="
pip install browser-use

python -c "from browser_use import Agent; print('browser-use OK')"

# Database + utility dependencies
echo ""
echo "=== Installing database + utility deps ==="
pip install psycopg2-binary pgvector imagehash beautifulsoup4 requests

# Verify all
echo ""
echo "=== Verification ==="
python -c "
import psycopg2; print('  psycopg2 OK')
import pgvector; print('  pgvector OK')
import imagehash; print('  imagehash OK')
import bs4; print('  beautifulsoup4 OK')
import requests; print('  requests OK')
from transformers import AutoModel; print('  transformers OK')
import torch; print('  torch OK')
from PIL import Image; print('  pillow OK')
from crawl4ai import AsyncWebCrawler; print('  crawl4ai OK')
from browser_use import Agent; print('  browser-use OK')
"

echo ""
echo "=== Setup complete! ==="
echo "Activate with: source $VENV_DIR/bin/activate"
