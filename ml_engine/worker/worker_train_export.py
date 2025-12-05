#!/usr/bin/env python3
# ml_engine/worker/worker_train_export.py
"""
Training worker that processes jobs end-to-end:
1. Polls for pending jobs
2. Runs smoke training
3. Exports model artifacts
4. Records artifacts to database
"""
import os
import sys
import time
import json
import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from train.smoke_trainer import tiny_train
from export.export_service import make_model_package


def get_db_connection():
    """Get PostgreSQL database connection."""
    database_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URL_LOCAL') or 'postgres://bioml_admin:bioml_pass@localhost:5432/biomlstudio'
    return psycopg2.connect(database_url)


def fetch_pending_job(conn):
    """
    Fetch a pending job and mark it as 'running'.
    Returns job record or None if no pending jobs.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Use FOR UPDATE SKIP LOCKED for concurrent workers
        cur.execute("""
            SELECT * FROM jobs 
            WHERE status = 'pending' 
            ORDER BY created_at ASC 
            LIMIT 1 
            FOR UPDATE SKIP LOCKED
        """)
        job = cur.fetchone()
        
        if job:
            # Mark as running
            cur.execute(
                "UPDATE jobs SET status='running', updated_at=now() WHERE id=%s",
                (job['id'],)
            )
            conn.commit()
            return dict(job)
    
    return None


def process_job(conn, job):
    """
    Process a single training job:
    1. Run smoke training
    2. Export model package
    3. Record artifact in DB
    4. Update job status
    """
    job_id = job['id']
    params = job.get('params', {})
    
    print(f"Processing job {job_id} with params: {params}")
    
    try:
        # Create working directory
        work_dir = f"data/tmp/{job_id}"
        os.makedirs(work_dir, exist_ok=True)
        
        # Run smoke training
        print(f"Running smoke training for job {job_id}...")
        epochs = params.get('epochs', 1) if isinstance(params, dict) else 1
        input_dim = params.get('input_dim', 8) if isinstance(params, dict) else 8
        
        weights_path, meta = tiny_train(work_dir, epochs=epochs, input_dim=input_dim)
        print(f"Training complete. Weights saved to {weights_path}")
        
        # Export model package
        print(f"Exporting model package for job {job_id}...")
        zip_path, manifest_path, checksum = make_model_package(
            job_id, 
            work_dir, 
            out_dir="data/models"
        )
        print(f"Model exported to {zip_path} with checksum {checksum}")
        
        # Record artifact in database
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO artifacts(job_id, path, checksum) 
                VALUES (%s, %s, %s)
                ON CONFLICT (job_id) DO UPDATE 
                SET path=EXCLUDED.path, checksum=EXCLUDED.checksum
            """, (job_id, zip_path, checksum))
        
        # Update job with results
        result_payload = {
            "artifact_path": zip_path,
            "manifest_path": manifest_path,
            "checksum": checksum,
            "meta": meta
        }
        
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE jobs 
                SET status='completed', 
                    result_payload=%s, 
                    updated_at=now() 
                WHERE id=%s
            """, (json.dumps(result_payload), job_id))
        
        conn.commit()
        print(f"Job {job_id} completed successfully")
        
        # Cleanup temp directory
        import shutil
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        
        return True
        
    except Exception as e:
        print(f"Job {job_id} failed with error: {e}")
        
        # Update job status to failed
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE jobs 
                    SET status='failed', 
                        result_payload=%s, 
                        updated_at=now() 
                    WHERE id=%s
                """, (json.dumps({"error": str(e)}), job_id))
            conn.commit()
        except Exception as update_error:
            print(f"Failed to update job status: {update_error}")
        
        return False


def main():
    """Main worker loop."""
    print("Starting training worker...")
    
    # Ensure data directories exist
    os.makedirs("data/tmp", exist_ok=True)
    os.makedirs("data/models", exist_ok=True)
    
    conn = None
    
    try:
        conn = get_db_connection()
        print("Database connection established")
        
        while True:
            try:
                # Fetch pending job
                job = fetch_pending_job(conn)
                
                if job:
                    # Process the job
                    process_job(conn, job)
                else:
                    # No jobs available, wait before polling again
                    time.sleep(2)
                    
            except Exception as e:
                print(f"Error in worker loop: {e}")
                time.sleep(5)
                
                # Try to reconnect if connection lost
                if conn.closed:
                    print("Reconnecting to database...")
                    conn = get_db_connection()
    
    except KeyboardInterrupt:
        print("\nWorker stopped by user")
    
    finally:
        if conn and not conn.closed:
            conn.close()
            print("Database connection closed")


if __name__ == "__main__":
    main()
