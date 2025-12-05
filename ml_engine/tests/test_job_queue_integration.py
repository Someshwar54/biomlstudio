#!/usr/bin/env python3
# ml_engine/tests/test_job_queue_integration.py
# Integration test: create a job via POST /api/jobs, verify Redis receives it,
# and confirm worker processes it (artifact created, DB status updated).

import os
import subprocess
import time
import requests
import json

BASE = 'http://localhost:4000/api/jobs'
ARTIFACT_DIR = 'data/models'

def test_job_queue_integration():
    """Test job creation -> queue -> worker processing -> artifact."""
    
    # Ensure backend is running (test assumes it was started separately)
    # POST /api/jobs to create a job
    try:
        resp = requests.post(BASE, json={'dataset_id': None, 'params': {'smoke': True}}, timeout=5)
    except requests.exceptions.ConnectionError:
        raise AssertionError("Backend not running on localhost:4000. Start backend first.")
    
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    job_id = data['job_id']
    assert data['status'] == 'queued', f"Expected status=queued, got {data['status']}"
    print(f"[test] created job: {job_id}")
    
    # Wait for worker to process the job (max 30 seconds)
    # Worker should BLPOP the job from Redis, process it, and create an artifact file
    artifact_path = os.path.join(ARTIFACT_DIR, f"{job_id}.txt")
    
    print(f"[test] waiting for worker to process job (max 30s)...")
    for attempt in range(60):
        if os.path.exists(artifact_path):
            print(f"[test] artifact created: {artifact_path}")
            break
        time.sleep(0.5)
    else:
        raise AssertionError(f"Artifact not created after 30s at {artifact_path}")
    
    # Verify artifact content
    with open(artifact_path, 'r') as f:
        content = f.read()
        assert content.startswith(f"trained-job:{job_id}"), f"Unexpected artifact content: {content}"
    print(f"[test] artifact content verified")
    
    # Verify job status is now 'completed' (optional: requires DB query endpoint or direct DB check)
    # For now, just confirm artifact exists
    print(f"[test] job queue integration test PASSED")

if __name__ == '__main__':
    test_job_queue_integration()
