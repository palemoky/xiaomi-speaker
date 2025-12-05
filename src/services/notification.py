"""Notification processing and orchestration service."""

import logging
from pathlib import Path
from typing import Dict, Optional

from src.config import settings
from src.services.speaker import SpeakerService
from src.services.tts import TTSService

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for processing and sending notifications."""

    def __init__(self) -> None:
        """Initialize the notification service."""
        self.tts = TTSService()
        self.speaker = SpeakerService()

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.speaker.close()

    def _format_notification(
        self,
        template: str,
        repo: str,
        workflow: str,
        conclusion: str,
        url: Optional[str] = None,
    ) -> str:
        """Format notification message from template.

        Args:
            template: Message template with placeholders
            repo: Repository name
            workflow: Workflow name
            conclusion: Workflow conclusion (success, failure, etc.)
            url: Optional workflow URL

        Returns:
            Formatted notification message
        """
        message = template.format(
            repo=repo,
            workflow=workflow,
            conclusion=conclusion,
            url=url or "",
        )
        return message

    async def send_github_notification(
        self,
        repo: str,
        workflow: str,
        conclusion: str,
        url: Optional[str] = None,
    ) -> bool:
        """Send a GitHub workflow notification.

        Args:
            repo: Repository name (e.g., "user/repo")
            workflow: Workflow name
            conclusion: Workflow conclusion (success, failure, etc.)
            url: Optional workflow URL

        Returns:
            True if notification was sent successfully
        """
        try:
            # Select template based on conclusion
            if conclusion == "failure":
                template = settings.notification_template_failure
            elif conclusion == "success":
                template = settings.notification_template_success
            else:
                # Generic template for other conclusions
                template = f"GitHub Actions 通知：仓库 {{repo}}，工作流 {{workflow}} 状态为 {conclusion}"

            # Format the message
            message = self._format_notification(
                template=template,
                repo=repo,
                workflow=workflow,
                conclusion=conclusion,
                url=url,
            )

            logger.info(f"Sending notification: {message}")

            # Generate audio using Edge TTS
            audio_file = await self.tts.generate_speech(message)

            # Get the audio URL for playback
            audio_url = self._get_audio_url(audio_file)

            # Play audio on speaker (now async)
            success = await self.speaker.play_audio_url(audio_url)

            if success:
                logger.info("Notification sent successfully")
            else:
                logger.error("Failed to send notification")

            return success

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    def _get_audio_url(self, audio_file: Path) -> str:
        """Get HTTP URL for audio file.

        Args:
            audio_file: Path to audio file

        Returns:
            HTTP URL for the audio file
        """
        # Get the filename relative to cache directory
        filename = audio_file.name

        # Construct URL using static server
        base_url = settings.get_static_server_url()
        return f"{base_url}/{filename}"

    async def send_custom_notification(self, message: str) -> bool:
        """Send a custom notification message.

        Args:
            message: Custom message to send

        Returns:
            True if notification was sent successfully
        """
        try:
            logger.info(f"Sending custom notification: {message}")

            # Generate audio using Edge TTS
            audio_file = await self.tts.generate_speech(message)

            # Get the audio URL for playback
            audio_url = self._get_audio_url(audio_file)

            # Play audio on speaker (now async)
            success = await self.speaker.play_audio_url(audio_url)

            if success:
                logger.info("Custom notification sent successfully")
            else:
                logger.error("Failed to send custom notification")

            return success

        except Exception as e:
            logger.error(f"Error sending custom notification: {e}")
            return False

