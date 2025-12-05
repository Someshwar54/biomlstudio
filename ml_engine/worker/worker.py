#!/usr/bin/env python3
# ml_engine/worker/worker.py
# Simple Redis-based job queue worker (consumer).
# Blocks on bioml:jobs list and processes jobs: updates DB status, writes artifact, marks complete.

import os
import sys
import time
import json
import hashlib
import psycopg2
import redis
from urllib.parse import urlparse

# Configuration from environment
DB_URL = os.getenv('DATABASE_URL', 'postgres://bioml_admin:bioml_pass@localhost:5432/biomlstudio')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
ARTIFACT_DIR = os.getenv('MODEL_ARTIFACT_PATH', 'data/models')

# Parse Redis URL and create connection
redis_url = urlparse(REDIS_URL)
redis_client = redis.Redis(
    host=redis_url.hostname or 'localhost',
    port=redis_url.port or 6379,
    db=int(redis_url.path.lstrip('/')) if redis_url.path else 0,
    decode_responses=True
)

def get_db_connection():
    """Create a fresh DB connection for the worker."""
    try:
        return psycopg2.connect(DB_URL)
    except Exception as e:
        print(f"[worker] DB connection failed: {e}")
        raise

def fetch_job(conn, job_id):
    """Fetch job record from DB."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, params, status FROM jobs WHERE id=%s", (job_id,))
        return cur.fetchone()

def update_job_status(conn, job_id, status):
    """Update job status in DB."""
    with conn.cursor() as cur:
        cur.execute("UPDATE jobs SET status=%s, updated_at=now() WHERE id=%s", (status, job_id))
    conn.commit()

def write_artifact(conn, job_id, payload):
    """
    Write artifact to disk and register in DB.
    Returns: (artifact_path, checksum)
    """
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    artifact_path = os.path.join(ARTIFACT_DIR, f"{job_id}.txt")
    
    # Write payload to disk
    with open(artifact_path, 'w') as f:
        f.write(payload)
    
    # Compute SHA256 checksum
    h = hashlib.sha256()
    with open(artifact_path, 'rb') as f:
        while True:
            block = f.read(65536)
            if not block:
                break
            h.update(block)
    checksum = h.hexdigest()
    
    # Record artifact in DB
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO artifacts(job_id, path, checksum) VALUES (%s, %s, %s)",
            (job_id, artifact_path, checksum)
        )
    conn.commit()
    
    print(f"[worker] artifact written: {artifact_path} (checksum: {checksum[:16]}...)")
    return artifact_path, checksum

def process_job(conn, job_id):
    """Process a single job: update status, run training, write artifact, mark done."""
    print(f"[worker] processing job: {job_id}")
    
    # Update status to running
    update_job_status(conn, job_id, 'running')
    
    # Simulate training: create a small result string
    payload = f"trained-job:{job_id} at {time.time()}"
    
    # Write artifact and record in DB
    artifact_path, checksum = write_artifact(conn, job_id, payload)
    
    # Update job with completed status and result
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE jobs SET status=%s, result_payload=%s, updated_at=now() WHERE id=%s",
            ('completed', json.dumps({'artifact': artifact_path, 'checksum': checksum}), job_id)
        )
    conn.commit()
    
    print(f"[worker] job completed: {job_id}")

def worker_loop():
    """Main worker loop: BLPOP from Redis queue and process jobs."""
    print("[worker] started, listening on bioml:jobs...")
    conn = None
    
    try:
        conn = get_db_connection()
        print("[worker] connected to database")
    except Exception as e:
        print(f"[worker] failed to connect to database: {e}, retrying...")
        time.sleep(5)
        return worker_loop()
    
    while True:
        try:
            # Block until a job arrives (timeout after 10s to allow reconnects)
            result = redis_client.brpop('bioml:jobs', timeout=10)
            if not result:
                # Timeout: continue loop (allows reconnection attempts)
                continue
            
            _, job_id = result
            print(f"[worker] got job from queue: {job_id}")
            
            # Process the job
            try:
                process_job(conn, job_id)
            except Exception as e:
                print(f"[worker] error processing job {job_id}: {e}")
                # Attempt to update DB status to failed (optional)
                try:
                    update_job_status(conn, job_id, 'failed')
                except:
                    pass
        
        except redis.ConnectionError as e:
            print(f"[worker] Redis connection lost: {e}, reconnecting...")
            time.sleep(5)
        except psycopg2.OperationalError as e:
            print(f"[worker] DB connection lost: {e}, reconnecting...")
            time.sleep(5)
            try:
                conn = get_db_connection()
            except:
                pass
        except Exception as e:
            print(f"[worker] unexpected error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    print("[worker] ML Engine job queue worker")
    try:
        worker_loop()
    except KeyboardInterrupt:
        print("[worker] shutting down")
        sys.exit(0)
