"""
Celery configuration for background task processing
"""

import logging
import ssl
import os
from celery import Celery
from celery.signals import setup_logging

from .config import settings

logger = logging.getLogger(__name__)

# Create broker folder for filesystem transport
os.makedirs("celery_broker/out", exist_ok=True)
os.makedirs("celery_broker/processed", exist_ok=True)

# Create Celery instance
celery_app = Celery(
    "biomlstudio",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.ml_tasks",
        "app.tasks.data_processing",
        "app.tasks.model_training"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_extended=True,
    timezone="UTC",
    enable_utc=True,
    
    # Disable task routing - use default queue
    task_default_queue='celery',
    task_create_missing_queues=True,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    
    # Task execution settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=settings.MAX_TRAINING_TIME_SECONDS,
    task_time_limit=settings.MAX_TRAINING_TIME_SECONDS + 60,
    broker_connection_retry_on_startup=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Security
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Enable TLS/SSL for Redis (Upstash uses TLS)
celery_app.conf.broker_use_ssl = {
    "ssl_cert_reqs": ssl.CERT_NONE,
}
celery_app.conf.redis_backend_use_ssl = {
    "ssl_cert_reqs": ssl.CERT_NONE,
}

# Transport options for SSL
celery_app.conf.broker_transport_options = {
    "ssl_cert_reqs": ssl.CERT_NONE,
}
celery_app.conf.result_backend_transport_options = {
    "ssl_cert_reqs": ssl.CERT_NONE,
}

@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Configure logging for Celery workers"""
    from logging.config import dictConfig
    
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s: %(levelname)s/%(name)s] %(message)s",
            },
        },
        "handlers": {
            "console": {
                "level": settings.LOG_LEVEL,
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "loggers": {
            "celery": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console"],
                "propagate": False,
            },
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console"],
        },
    })


# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-expired-jobs": {
        "task": "app.tasks.maintenance.cleanup_expired_jobs",
        "schedule": 3600.0,  # Every hour
    },
    "update-model-metrics": {
        "task": "app.tasks.maintenance.update_model_metrics",
        "schedule": 1800.0,  # Every 30 minutes
    },
    "health-check": {
        "task": "app.tasks.maintenance.health_check",
        "schedule": 300.0,  # Every 5 minutes
    },
}
