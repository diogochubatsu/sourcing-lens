#!/usr/bin/env python3
"""Quick test: verify backend imports and routes."""
import sys
import os

# Match the path setup in main.py
backend_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(backend_dir)
project_root = os.path.dirname(app_dir)

sys.path.insert(0, os.path.join(project_root, "scripts"))
sys.path.insert(0, project_root)

# Load .env
env_path = os.path.join(project_root, "config", ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

print("1. Testing imports...")
from matching import search_similar
from margins import calculate_margin
print("   OK — matching + margins imported")

print("2. Testing FastAPI app...")
from main import app
print("   OK — FastAPI app loaded")

print("3. Routes:")
for route in app.routes:
    if hasattr(route, "methods"):
        for m in route.methods:
            print(f"   {m:6s} {route.path}")

print("\nAll checks passed!")
