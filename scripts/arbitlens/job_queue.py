#!/usr/bin/env python3
"""
Simple job queue for background tasks.

Usage:
  from job_queue import submit_job, get_job_status
"""
import json
import os
import time
import uuid

_JOBS_DIR = os.path.join(os.path.dirname(__file__), 'output', 'jobs')

def _ensure_dir():
    os.makedirs(_JOBS_DIR, exist_ok=True)

def submit_job(job_type, params=None):
    """Submit a background job."""
    _ensure_dir()
    job_id = str(uuid.uuid4())[:8]
    job = {
        'id': job_id,
        'type': job_type,
        'params': params or {},
        'status': 'pending',
        'created_at': time.time(),
        'started_at': None,
        'completed_at': None,
        'result': None,
        'error': None,
    }
    with open(os.path.join(_JOBS_DIR, f'{job_id}.json'), 'w') as f:
        json.dump(job, f)
    return job_id

def get_job_status(job_id):
    """Get job status."""
    job_file = os.path.join(_JOBS_DIR, f'{job_id}.json')
    if not os.path.exists(job_file):
        return None
    with open(job_file) as f:
        return json.load(f)

def update_job(job_id, status=None, result=None, error=None):
    """Update job status."""
    job_file = os.path.join(_JOBS_DIR, f'{job_id}.json')
    if not os.path.exists(job_file):
        return
    with open(job_file) as f:
        job = json.load(f)
    if status:
        job['status'] = status
    if status == 'running':
        job['started_at'] = time.time()
    if status in ('completed', 'failed'):
        job['completed_at'] = time.time()
    if result:
        job['result'] = result
    if error:
        job['error'] = error
    with open(job_file, 'w') as f:
        json.dump(job, f)

def list_jobs(limit=10):
    """List recent jobs."""
    _ensure_dir()
    jobs = []
    for fname in sorted(os.listdir(_JOBS_DIR), reverse=True)[:limit]:
        if fname.endswith('.json'):
            with open(os.path.join(_JOBS_DIR, fname)) as f:
                jobs.append(json.load(f))
    return jobs
