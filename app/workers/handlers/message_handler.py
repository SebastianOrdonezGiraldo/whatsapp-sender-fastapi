"""Handlers for message-related background tasks."""

from typing import Dict, Any
from rq.job import Job

from app.core.logging import get_logger

logger = get_logger(__name__)


def handle_message_job_success(job: Job, connection, result: Dict[str, Any], *args, **kwargs) -> None:
    """
    Handle successful message job completion.
    
    Args:
        job: RQ Job instance
        connection: Redis connection
        result: Job result
        *args: Additional arguments
        **kwargs: Additional keyword arguments
    """
    logger.debug(
        "Message job completed successfully",
        job_id=job.id,
        message_id=result.get("message_id"),
        success=result.get("success"),
    )


def handle_message_job_failure(job: Job, connection, type, value, traceback, *args, **kwargs) -> None:
    """
    Handle message job failure.
    
    Args:
        job: RQ Job instance
        connection: Redis connection
        type: Exception type
        value: Exception value
        traceback: Traceback object
        *args: Additional arguments
        **kwargs: Additional keyword arguments
    """
    logger.error(
        "Message job failed",
        job_id=job.id,
        message_id=job.args[0] if job.args else None,
        error_type=str(type),
        error_value=str(value),
        exc_info=(type, value, traceback),
    )


def handle_message_job_started(job: Job, *args, **kwargs) -> None:
    """
    Handle message job start.
    
    Args:
        job: RQ Job instance
        *args: Additional arguments
        **kwargs: Additional keyword arguments
    """
    logger.debug(
        "Message job started",
        job_id=job.id,
        message_id=job.args[0] if job.args else None,
    )

