# ml_engine/tests/test_smoke_train_export.py
import os
import sys
import json
import tempfile
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ml_engine.train.smoke_trainer import SmokeTrainer
from ml_engine.export.export_service import ModelExportService

def test_smoke_trainer_trains_model():
    trainer = SmokeTrainer()
    model, loss = trainer.train()
    assert model is not None
    assert isinstance(loss, float)
    assert loss >= 0.0

def test_export_service_exports_model():
    with tempfile.TemporaryDirectory() as tmpdir:
        exporter = ModelExportService(export_dir=tmpdir)
        trainer = SmokeTrainer()
        model, _ = trainer.train()

        job_id = "test-job-123"
        model_path, manifest_path, checksum = exporter.export_model(model, job_id)

        # Check files exist
        assert os.path.exists(model_path)
        assert os.path.exists(manifest_path)

        # Check manifest content
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert manifest['job_id'] == job_id
        assert manifest['model_path'] == model_path
        assert manifest['checksum'] == checksum
        assert 'final_loss' not in manifest['metadata']  # Since we didn't pass metadata

def test_full_smoke_train_export_flow():
    with tempfile.TemporaryDirectory() as tmpdir:
        exporter = ModelExportService(export_dir=tmpdir)
        trainer = SmokeTrainer()
        model, loss = trainer.train()

        job_id = "test-job-456"
        model_path, manifest_path, checksum = exporter.export_model(
            model, job_id, metadata={'final_loss': loss}
        )

        # Verify files
        assert os.path.exists(model_path)
        assert os.path.exists(manifest_path)

        # Verify manifest
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert manifest['metadata']['final_loss'] == loss