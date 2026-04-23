"""
Pytest configuration and fixtures for BioMLStudio tests
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User
from app.models.dataset import Dataset
from app.models.job import Job
from app.models.ml_model import MLModel
from app.services.auth_service import AuthService
from app.core.security import get_password_hash


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_bioml.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraints for SQLite"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database tables at session start"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session):
    """Create an async test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_service():
    """Authentication service fixture"""
    return AuthService()


@pytest.fixture
def test_user_data():
    """Test user data fixture"""
    return {
        "email": "testuser@example.com",
        "full_name": "Test User",
        "password": "StrongPassword123!"
    }


@pytest.fixture
def test_user(db_session, test_user_data):
    """Create a test user"""
    user = User(
        email=test_user_data["email"],
        full_name=test_user_data["full_name"],
        hashed_password=get_password_hash(test_user_data["password"]),
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin test user"""
    admin = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("AdminPassword123!"),
        is_active=True,
        is_verified=True,
        is_admin=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def authenticated_client(client, test_user, auth_service):
    """Client with authentication token"""
    token = auth_service.create_access_token_for_user(test_user)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def admin_client(client, admin_user, auth_service):
    """Admin client with authentication token"""
    token = auth_service.create_access_token_for_user(admin_user)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def test_dataset_data():
    """Test dataset data fixture"""
    return {
        "name": "Test Dataset",
        "description": "A test dataset for unit tests",
        "dataset_type": "dna",
        "is_public": False
    }


@pytest.fixture
def sample_fasta_content():
    """Sample FASTA file content for testing"""
    return """>sequence1|promoter
ATGCGATCGATCGATCGATCG
>sequence2|non_promoter
GCTAGCTAGCTAGCTAGCTA
>sequence3|promoter
TTTTAAAACCCCGGGGAAAA
>sequence4|non_promoter
CCCGGGAAATTTCCCGGGAA
""".strip()


@pytest.fixture
def sample_csv_content():
    """Sample CSV file content for testing"""
    return """sequence,label,length
ATGCGATCGATCGATCGATCG,1,20
GCTAGCTAGCTAGCTAGCTA,0,20
TTTTAAAACCCCGGGGAAAA,1,20
CCCGGGAAATTTCCCGGGAA,0,20
"""


@pytest.fixture
def temp_fasta_file(sample_fasta_content):
    """Create temporary FASTA file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(sample_fasta_content)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_csv_file(sample_csv_content):
    """Create temporary CSV file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(sample_csv_content)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def test_dataset(db_session, test_user, test_dataset_data, temp_fasta_file):
    """Create a test dataset"""
    dataset = Dataset(
        user_id=test_user.id,
        name=test_dataset_data["name"],
        description=test_dataset_data["description"],
        dataset_type=test_dataset_data["dataset_type"],
        filename="test.fasta",
        file_path=str(temp_fasta_file),
        file_size=temp_fasta_file.stat().st_size,
        file_extension=".fasta",
        is_public=test_dataset_data["is_public"],
        processing_status="ready",
        is_validated=True
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset


@pytest.fixture
def test_job_config():
    """Test job configuration fixture"""
    return {
        "model_type": "classification",
        "algorithm": "random_forest",
        "test_size": 0.2,
        "target_column": "label",
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 10,
            "random_state": 42
        }
    }


@pytest.fixture
def test_job(db_session, test_user, test_dataset, test_job_config):
    """Create a test job"""
    job = Job(
        user_id=test_user.id,
        dataset_id=test_dataset.id,
        name="Test Training Job",
        description="A test training job",
        job_type="training",
        config=test_job_config,
        status="pending"
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def test_model(db_session, test_user, test_job):
    """Create a test ML model"""
    model = MLModel(
        user_id=test_user.id,
        name="Test Model",
        description="A test ML model",
        model_type="classification",
        framework="scikit_learn",
        algorithm="random_forest",
        metrics={
            "accuracy": 0.95,
            "precision": 0.94,
            "recall": 0.96,
            "f1_score": 0.95
        },
        training_samples_count=800,
        validation_samples_count=200,
        is_active=True
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    
    # Link model to job
    test_job.model_id = model.id
    db_session.commit()
    
    return model


@pytest.fixture
def mock_celery_task(monkeypatch):
    """Mock Celery task execution for testing"""
    class MockAsyncResult:
        def __init__(self, task_id="test-task-id"):
            self.id = task_id
            self.status = "SUCCESS"
            self.result = {"status": "completed"}
        
        def get(self, timeout=None):
            return self.result
    
    def mock_delay(*args, **kwargs):
        return MockAsyncResult()
    
    # Mock various task delays
    monkeypatch.setattr("app.tasks.ml_tasks.start_training_task.delay", mock_delay)
    monkeypatch.setattr("app.tasks.data_processing.process_biological_data_task.delay", mock_delay)
    monkeypatch.setattr("app.tasks.model_training.hyperparameter_tuning_task.delay", mock_delay)
    
    return mock_delay


@pytest.fixture
def mock_storage_service(monkeypatch):
    """Mock storage service for testing"""
    class MockStorageService:
        async def upload_file(self, file_path, object_name, metadata=None):
            return f"mocked/path/{object_name}"
        
        async def download_file(self, object_name, file_path):
            return True
        
        async def delete_file(self, object_name):
            return True
        
        async def get_file_info(self, object_name):
            return {
                "name": object_name,
                "size": 1024,
                "content_type": "application/octet-stream"
            }
    
    mock_service = MockStorageService()
    monkeypatch.setattr("app.services.storage_service.StorageService", lambda: mock_service)
    return mock_service


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Pytest configuration
pytest_plugins = ["pytest_asyncio"]
