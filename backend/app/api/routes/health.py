"""
Health check endpoints for monitoring and load balancer health checks
"""

import logging
import time
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Dict: Health status information
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time()
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check that verifies database connectivity.
    
    Args:
        db: Database session
        
    Returns:
        Dict: Detailed health status
        
    Raises:
        HTTPException: If any health check fails
    """
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Database health check
    try:
        start_time = time.time()
        result = db.execute(text("SELECT 1"))
        db_response_time = time.time() - start_time
        
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_response_time * 1000, 2)
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check available disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_percent = (free / total) * 100
        
        health_status["checks"]["disk_space"] = {
            "status": "healthy" if free_percent > 10 else "warning",
            "free_percent": round(free_percent, 2),
            "free_gb": round(free / (1024**3), 2)
        }
    except Exception as e:
        logger.warning(f"Disk space check failed: {e}")
        health_status["checks"]["disk_space"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # Memory usage check
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        health_status["checks"]["memory"] = {
            "status": "healthy" if memory.percent < 90 else "warning",
            "used_percent": memory.percent,
            "available_gb": round(memory.available / (1024**3), 2)
        }
    except ImportError:
        # psutil not available
        health_status["checks"]["memory"] = {
            "status": "unknown",
            "error": "psutil not available"
        }
    except Exception as e:
        logger.warning(f"Memory check failed: {e}")
        health_status["checks"]["memory"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # If any critical check failed, return 503
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint.
    
    Args:
        db: Database session
        
    Returns:
        Dict: Readiness status
    """
    try:
        # Quick database connectivity check
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not ready",
                "error": str(e),
                "timestamp": time.time()
            }
        )


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        Dict: Liveness status
    """
    return {
        "status": "alive",
        "timestamp": str(time.time())
    }
