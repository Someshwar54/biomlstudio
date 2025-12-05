#!/usr/bin/env python3
# ml_engine/tests/test_smoke_train_export.py
"""
Integration test for smoke training and model export.
Tests the full workflow: job creation -> worker training -> export -> DB record
"""
import os
import sys
import time
import json
import hashlib
import subprocess
import requests
import psycopg2


BASE_URL = 'http://localhost:4000'
JOBS_API = f'{BASE_URL}/api/jobs'


def wait_server_ready(url=f'{BASE_URL}/healthz', timeout=15):
    """Wait for backend server to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print("Backend server ready")
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def get_db_connection():
    """Get database connection."""
    database_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URL_LOCAL') or 'postgres://bioml_admin:bioml_pass@localhost:5432/biomlstudio'
    return psycopg2.connect(database_url)


def compute_file_checksum(path):
    """Compute SHA256 checksum of a file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def test_smoke_train_export():
    """
    Main integration test:
    1. Start backend server
    2. Start worker
    3. Create a job
    4. Wait for artifact to be created
    5. Verify artifact exists and DB record is correct
    """
    
    # Start backend server
    print("Starting backend server...")
    backend_proc = subprocess.Popen(
        ['node', 'backend/src/server.js'],
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    # Start worker process
    print("Starting worker...")
    worker_proc = subprocess.Popen(
        [sys.executable, 'ml_engine/worker/worker_train_export.py'],
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    try:
        # Wait for server to be ready
        assert wait_server_ready(), "Backend server did not start in time"
        
        # Give worker a moment to initialize
        time.sleep(2)
        
        # Create a job via API
        print("Creating job...")
        r = requests.post(JOBS_API, json={
            'dataset_id': None,
            'params': {'smoke': True, 'epochs': 1, 'input_dim': 8}
        })
        assert r.status_code == 201, f"Job creation failed: {r.status_code} {r.text}"
        
        job_data = r.json()
        job_id = job_data['job_id']
        print(f"Job created with ID: {job_id}")
        
        # Wait for artifact to be created (up to 30 seconds)
        artifact_path = f"data/models/model-{job_id}.zip"
        manifest_path = f"data/models/model-{job_id}-manifest.json"
        
        print(f"Waiting for artifact {artifact_path}...")
        for i in range(30):
            if os.path.exists(artifact_path):
                print(f"Artifact found after {i+1} seconds")
                break
            time.sleep(1)
        else:
            raise AssertionError(f"Artifact {artifact_path} was not created within 30 seconds")
        
        # Verify artifact exists
        assert os.path.exists(artifact_path), f"Model zip missing: {artifact_path}"
        assert os.path.getsize(artifact_path) > 0, "Model zip is empty"
        print(f"✓ Artifact exists: {artifact_path}")
        
        # Verify manifest exists
        assert os.path.exists(manifest_path), f"Manifest missing: {manifest_path}"
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        assert manifest['job_id'] == job_id, "Manifest job_id mismatch"
        assert 'checksum' in manifest, "Manifest missing checksum"
        print(f"✓ Manifest exists: {manifest_path}")
        
        # Compute actual checksum
        actual_checksum = compute_file_checksum(artifact_path)
        assert actual_checksum == manifest['checksum'], "Checksum mismatch between file and manifest"
        print(f"✓ Checksum matches: {actual_checksum[:16]}...")
        
        # Check database for artifact record
        print("Checking database...")
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT path, checksum FROM artifacts WHERE job_id=%s",
                (job_id,)
            )
            row = cur.fetchone()
            
            assert row is not None, f"No artifact record found in DB for job {job_id}"
            db_path, db_checksum = row
            
            assert os.path.exists(db_path), f"Path in DB doesn't exist: {db_path}"
            assert db_checksum == actual_checksum, f"DB checksum mismatch: {db_checksum} vs {actual_checksum}"
            print(f"✓ DB record exists with matching checksum")
            
            # Check job status
            cur.execute("SELECT status, result_payload FROM jobs WHERE id=%s", (job_id,))
            job_row = cur.fetchone()
            assert job_row is not None, "Job not found in DB"
            assert job_row[0] == 'completed', f"Job status is {job_row[0]}, expected 'completed'"
            print(f"✓ Job status is 'completed'")
            
        finally:
            conn.close()
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    
    finally:
        # Cleanup processes
        print("\nCleaning up...")
        worker_proc.terminate()
        backend_proc.terminate()
        
        try:
            worker_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker_proc.kill()
        
        try:
            backend_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_proc.kill()
        
        print("Cleanup complete")


if __name__ == "__main__":
    try:
        test_smoke_train_export()
        sys.exit(0)
    except Exception as e:
        print(f"Test failed: {e}", file=sys.stderr)
        sys.exit(1)
