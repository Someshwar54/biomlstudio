# ml_engine/export/export_service.py
import os
import json
import hashlib
import torch
from datetime import datetime, timezone

class ModelExportService:
    def __init__(self, export_dir='data/models'):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)

    def export_model(self, model, job_id, metadata=None):
        """
        Export model to disk with manifest and checksum.
        Returns: (model_path, manifest_path, checksum)
        """
        # Save model
        model_path = os.path.join(self.export_dir, f"{job_id}.pt")
        torch.save(model.state_dict(), model_path)

        # Compute checksum
        checksum = self._compute_checksum(model_path)

        # Create manifest
        manifest = {
            'job_id': job_id,
            'model_path': model_path,
            'checksum': checksum,
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata or {}
        }
        manifest_path = os.path.join(self.export_dir, f"{job_id}_manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        return model_path, manifest_path, checksum

    def _compute_checksum(self, file_path):
        h = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                block = f.read(65536)
                if not block:
                    break
                h.update(block)
        return h.hexdigest()