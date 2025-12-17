"""Tests for API webhook endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_notification():
    """Mock notification service."""
    with patch("src.api.webhooks.notification") as mock:
        mock.send_github_notification = AsyncMock(return_value=True)
        mock.send_custom_notification = AsyncMock(return_value=True)
        yield mock


class TestCustomWebhook:
    """Tests for /webhook/custom endpoint."""

    def test_custom_notification_success(self, client, mock_notification):
        """Test successful custom notification with valid API key."""
        with patch("src.api.webhooks.settings") as mock_settings:
            mock_settings.api_secret = "test_secret"

            response = client.post(
                "/webhook/custom",
                json={"message": "Test notification"},
                headers={"X-API-Key": "test_secret"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processed"
            assert data["notification_sent"] is True
            assert data["message"] == "Test notification"

    def test_custom_notification_missing_api_key(self, client):
        """Test custom notification without API key."""
        with patch("src.api.webhooks.settings") as mock_settings:
            mock_settings.api_secret = "test_secret"

            response = client.post("/webhook/custom", json={"message": "Test notification"})

            assert response.status_code == 401
            assert "Missing X-API-Key header" in response.json()["detail"]

    def test_custom_notification_invalid_api_key(self, client):
        """Test custom notification with invalid API key."""
        with patch("src.api.webhooks.settings") as mock_settings:
            mock_settings.api_secret = "test_secret"

            response = client.post(
                "/webhook/custom",
                json={"message": "Test notification"},
                headers={"X-API-Key": "wrong_key"},
            )

            assert response.status_code == 403
            assert "Invalid API key" in response.json()["detail"]

    def test_custom_notification_no_api_secret_configured(self, client, mock_notification):
        """Test custom notification when API secret is not configured."""
        with patch("src.api.webhooks.settings") as mock_settings:
            mock_settings.api_secret = None

            response = client.post("/webhook/custom", json={"message": "Test notification"})

            assert response.status_code == 200

    def test_custom_notification_missing_message(self, client):
        """Test custom notification without message field."""
        with patch("src.api.webhooks.settings") as mock_settings:
            mock_settings.api_secret = "test_secret"

            response = client.post("/webhook/custom", json={}, headers={"X-API-Key": "test_secret"})

            assert response.status_code == 400
            assert "Missing 'message' field" in response.json()["detail"]

    def test_custom_notification_invalid_json(self, client):
        """Test custom notification with invalid JSON."""
        with patch("src.api.webhooks.settings") as mock_settings:
            mock_settings.api_secret = "test_secret"

            response = client.post(
                "/webhook/custom",
                content="invalid json",
                headers={"X-API-Key": "test_secret", "Content-Type": "application/json"},
            )

            assert response.status_code == 400


class TestGitHubWebhook:
    """Tests for /webhook/github endpoint."""

    def test_workflow_run_completed_success(self, client, mock_notification):
        """Test workflow_run event with success conclusion."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "name": "CI",
                "conclusion": "success",
                "repository": {"full_name": "user/repo"},
                "html_url": "https://github.com/user/repo/actions/runs/123",
            },
        }

        response = client.post(
            "/webhook/github", json=payload, headers={"X-GitHub-Event": "workflow_run"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert data["notification_sent"] is True

    def test_workflow_run_completed_failure(self, client, mock_notification):
        """Test workflow_run event with failure conclusion."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "name": "CI",
                "conclusion": "failure",
                "repository": {"full_name": "user/repo"},
                "html_url": "https://github.com/user/repo/actions/runs/123",
            },
        }

        response = client.post(
            "/webhook/github", json=payload, headers={"X-GitHub-Event": "workflow_run"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"

    def test_workflow_run_ignored_action(self, client):
        """Test workflow_run event with non-completed action."""
        payload = {
            "action": "in_progress",
            "workflow_run": {
                "name": "CI",
                "conclusion": None,
                "repository": {"full_name": "user/repo"},
            },
        }

        response = client.post(
            "/webhook/github", json=payload, headers={"X-GitHub-Event": "workflow_run"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

    def test_unsupported_event_type(self, client):
        """Test unsupported GitHub event type."""
        payload = {"action": "opened"}

        response = client.post(
            "/webhook/github", json=payload, headers={"X-GitHub-Event": "pull_request"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

    def test_invalid_json_payload(self, client):
        """Test GitHub webhook with invalid JSON."""
        response = client.post(
            "/webhook/github",
            content="invalid json",
            headers={"X-GitHub-Event": "workflow_run", "Content-Type": "application/json"},
        )

        assert response.status_code == 400


class TestAPIKeyVerification:
    """Tests for API key verification function."""

    @pytest.mark.asyncio
    async def test_verify_api_key_valid(self):
        """Test API key verification with valid key."""
        from src.api.webhooks import verify_api_key

        with patch("src.api.webhooks.settings") as mock_settings:
            mock_settings.api_secret = "test_secret"

            result = await verify_api_key(x_api_key="test_secret")
            assert result == "test_secret"

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid(self):
        """Test API key verification with invalid key."""
        from fastapi import HTTPException

        from src.api.webhooks import verify_api_key

        with patch("src.api.webhooks.settings") as mock_settings:
            mock_settings.api_secret = "test_secret"

            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(x_api_key="wrong_key")

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_verify_api_key_missing(self):
        """Test API key verification with missing key."""
        from fastapi import HTTPException

        from src.api.webhooks import verify_api_key

        with patch("src.api.webhooks.settings") as mock_settings:
            mock_settings.api_secret = "test_secret"

            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(x_api_key=None)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_api_key_not_configured(self):
        """Test API key verification when not configured."""
        from src.api.webhooks import verify_api_key

        with patch("src.api.webhooks.settings") as mock_settings:
            mock_settings.api_secret = None

            result = await verify_api_key(x_api_key=None)
            assert result == "not_configured"
