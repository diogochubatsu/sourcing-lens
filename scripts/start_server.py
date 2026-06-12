#!/usr/bin/env python3
"""Start ArbitLens server with proper locale on port 8080."""
import os, sys
os.environ.pop('LC_ALL', None)
os.environ['LC_ALL'] = 'C.UTF-8'
sys.path.insert(0, '/mnt/ssd/arbitlens')
import uvicorn
from app.backend.main import app
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080, log_level='warning')
