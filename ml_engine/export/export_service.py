# ml_engine/export/export_service.py
import os
import json
import zipfile
import hashlib
import time
from pathlib import Path


def compute_sha256(path):
    """
    Compute SHA256 checksum of a file.
    """
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def make_model_package(job_id, src_dir, out_dir="data/models"):
    """
    Package model artifacts into a zip file with manifest and checksum.
    
    Args:
        job_id: Unique job identifier
        src_dir: Directory containing model files (weights.pt, meta.json, etc.)
        out_dir: Output directory for packaged model
    
    Returns:
        tuple: (zip_path, manifest_path, checksum)
    """
    os.makedirs(out_dir, exist_ok=True)
    
    zip_name = f"model-{job_id}.zip"
    zip_path = os.path.join(out_dir, zip_name)
    
    # Build manifest
    manifest = {
        "job_id": str(job_id),
        "created_at": time.time(),
        "files": []
    }
    
    # Create zip atomically (write to .part then rename)
    temp_zip_path = zip_path + ".part"
    with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        src_path = Path(src_dir)
        for file_path in src_path.iterdir():
            if file_path.is_file():
                z.write(file_path, arcname=file_path.name)
                manifest["files"].append(str(file_path.name))
    
    # Atomically move to final location
    os.replace(temp_zip_path, zip_path)
    
    # Compute checksum of the final zip
    checksum = compute_sha256(zip_path)
    manifest["checksum"] = checksum
    
    # Write manifest file
    manifest_path = os.path.join(out_dir, f"model-{job_id}-manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    return zip_path, manifest_path, checksum
