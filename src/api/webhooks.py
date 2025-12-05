"""FastAPI webhook endpoints for GitHub notifications."""

import hashlib
import hmac
import logging
import secrets
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from src.config import settings
from src.services.notification import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])

# Global notification service instance
notification = NotificationService()


def verify_github_signature(
    payload: bytes,
    signature: Optional[str],
    secret: str,
) -> bool:
    """Verify GitHub webhook signature.

    Args:
        payload: Request payload bytes
        signature: GitHub signature from header
        secret: Webhook secret

    Returns:
        True if signature is valid
    """
    if not signature:
        return False

    # GitHub signature format: sha256=<hash>
    if not signature.startswith("sha256="):
        return False

    expected_signature = signature.split("=")[1]

    # Compute HMAC
    mac = hmac.new(
        secret.encode(),
        msg=payload,
        digestmod=hashlib.sha256,
    )
    computed_signature = mac.hexdigest()

    return hmac.compare_digest(computed_signature, expected_signature)


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify API key from request header.
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        The verified API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    # If API secret is not configured, skip verification
    if not settings.api_secret:
        logger.warning("API_SECRET not configured, skipping authentication")
        return "not_configured"
    
    if x_api_key is None:
        logger.warning("Missing API key in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header"
        )
    
    # Use secrets.compare_digest for secure string comparison
    if not secrets.compare_digest(x_api_key, settings.api_secret):
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return x_api_key


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Handle GitHub webhook events.

    Args:
        request: FastAPI request object
        x_github_event: GitHub event type from header
        x_hub_signature_256: GitHub signature from header

    Returns:
        Response dictionary

    Raises:
        HTTPException: If signature verification fails or processing error occurs
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify signature if secret is configured
    if settings.github_webhook_secret:
        if not verify_github_signature(
            body,
            x_hub_signature_256,
            settings.github_webhook_secret,
        ):
            logger.warning("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    logger.info(f"Received GitHub event: {x_github_event}")

    # Process workflow_run events
    if x_github_event == "workflow_run":
        return await handle_workflow_run(payload)

    # Process workflow_job events
    elif x_github_event == "workflow_job":
        return await handle_workflow_job(payload)

    # Process check_run events
    elif x_github_event == "check_run":
        return await handle_check_run(payload)

    else:
        logger.info(f"Ignoring event type: {x_github_event}")
        return {"status": "ignored", "event": x_github_event}


async def handle_workflow_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle workflow_run events.

    Args:
        payload: Webhook payload

    Returns:
        Response dictionary
    """
    action = payload.get("action")
    workflow_run = payload.get("workflow_run", {})

    # Only process completed workflows
    if action != "completed":
        logger.info(f"Ignoring workflow_run action: {action}")
        return {"status": "ignored", "action": action}

    # Extract workflow information
    workflow_name = workflow_run.get("name", "Unknown")
    conclusion = workflow_run.get("conclusion", "unknown")
    repo_name = workflow_run.get("repository", {}).get("full_name", "Unknown")
    workflow_url = workflow_run.get("html_url")

    logger.info(
        f"Workflow completed - Repo: {repo_name}, "
        f"Workflow: {workflow_name}, Conclusion: {conclusion}"
    )

    # Send notification
    success = await notification.send_github_notification(
        repo=repo_name,
        workflow=workflow_name,
        conclusion=conclusion,
        url=workflow_url,
    )

    return {
        "status": "processed",
        "notification_sent": success,
        "workflow": workflow_name,
        "conclusion": conclusion,
    }


async def handle_workflow_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle workflow_job events.

    Args:
        payload: Webhook payload

    Returns:
        Response dictionary
    """
    action = payload.get("action")
    workflow_job = payload.get("workflow_job", {})

    # Only process completed jobs
    if action != "completed":
        logger.info(f"Ignoring workflow_job action: {action}")
        return {"status": "ignored", "action": action}

    # Extract job information
    job_name = workflow_job.get("name", "Unknown")
    conclusion = workflow_job.get("conclusion", "unknown")
    repo_name = payload.get("repository", {}).get("full_name", "Unknown")
    job_url = workflow_job.get("html_url")

    logger.info(
        f"Job completed - Repo: {repo_name}, "
        f"Job: {job_name}, Conclusion: {conclusion}"
    )

    # Send notification
    success = await notification.send_github_notification(
        repo=repo_name,
        workflow=job_name,
        conclusion=conclusion,
        url=job_url,
    )

    return {
        "status": "processed",
        "notification_sent": success,
        "job": job_name,
        "conclusion": conclusion,
    }


async def handle_check_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle check_run events.

    Args:
        payload: Webhook payload

    Returns:
        Response dictionary
    """
    action = payload.get("action")
    check_run = payload.get("check_run", {})

    # Only process completed checks
    if action != "completed":
        logger.info(f"Ignoring check_run action: {action}")
        return {"status": "ignored", "action": action}

    # Extract check information
    check_name = check_run.get("name", "Unknown")
    conclusion = check_run.get("conclusion", "unknown")
    repo_name = payload.get("repository", {}).get("full_name", "Unknown")
    check_url = check_run.get("html_url")

    logger.info(
        f"Check completed - Repo: {repo_name}, "
        f"Check: {check_name}, Conclusion: {conclusion}"
    )

    # Send notification
    success = await notification.send_github_notification(
        repo=repo_name,
        workflow=check_name,
        conclusion=conclusion,
        url=check_url,
    )

    return {
        "status": "processed",
        "notification_sent": success,
        "check": check_name,
        "conclusion": conclusion,
    }


@router.post("/custom")
async def custom_notification(
    request: Request,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Send a custom notification.

    Args:
        request: FastAPI request with JSON body containing "message" field
        api_key: Verified API key from header (injected by dependency)

    Returns:
        Response dictionary

    Raises:
        HTTPException: If message is missing or processing fails
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    message = payload.get("message")
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'message' field",
        )

    logger.info(f"Sending custom notification: {message}")

    success = await notification.send_custom_notification(message)

    return {
        "status": "processed",
        "notification_sent": success,
        "message": message,
    }
