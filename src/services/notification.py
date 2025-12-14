"""Notification processing and orchestration service."""

import asyncio
import logging
from pathlib import Path

from src.config import settings
from src.services.speaker import SpeakerService
from src.services.tts import TTSService
from src.utils.language import is_chinese

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for processing and sending notifications."""

    def __init__(self) -> None:
        """Initialize the notification service."""
        self.tts = TTSService()
        self.speaker = SpeakerService()
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.worker_task: asyncio.Task | None = None
        self._shutdown = False

    def start_worker(self) -> None:
        """Start the background worker to process notification queue."""
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._queue_worker())
            logger.info("Notification queue worker started")

    async def _queue_worker(self) -> None:
        """Background worker that processes notifications from the queue."""
        logger.info("Queue worker running")
        while not self._shutdown:
            try:
                # Wait for a message with timeout to allow checking shutdown flag
                try:
                    message = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except TimeoutError:
                    continue

                # Process the message
                try:
                    await self._send_message(message)
                except Exception as e:
                    logger.error(f"Error processing notification: {e}", exc_info=True)
                finally:
                    self.queue.task_done()

                # Wait for configured interval before processing next message
                if settings.notification_interval > 0:
                    await asyncio.sleep(settings.notification_interval)

            except Exception as e:
                logger.error(f"Queue worker error: {e}", exc_info=True)
                await asyncio.sleep(1.0)  # Prevent tight loop on errors

        logger.info("Queue worker stopped")

    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up notification service...")
        self._shutdown = True

        # Wait for queue to be processed
        if not self.queue.empty():
            logger.info(f"Waiting for {self.queue.qsize()} queued notifications to complete...")
            await self.queue.join()

        # Cancel worker task
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

        await self.speaker.close()
        logger.info("Notification service cleanup complete")

    def _format_notification(
        self,
        template: str,
        repo: str,
        workflow: str,
        conclusion: str,
        url: str | None = None,
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

    async def _send_message(self, message: str) -> bool:
        """Send a message using appropriate TTS method.

        Args:
            message: Message to send

        Returns:
            True if message was sent successfully
        """
        # Check if we should use speaker's built-in TTS
        if self._should_use_speaker_tts(message):
            logger.info("Using speaker's built-in TTS for Chinese")
            return await self.speaker.play_tts(message)
        else:
            # Generate audio using Piper TTS
            audio_file = await self.tts.generate_speech(message)
            # Get the audio URL for playback
            audio_url = self._get_audio_url(audio_file)
            # Play audio on speaker
            return await self.speaker.play_audio_url(audio_url)

    async def send_github_notification(
        self,
        repo: str,
        workflow: str,
        conclusion: str,
        url: str | None = None,
    ) -> bool:
        """Send a GitHub workflow notification.

        Args:
            repo: Repository name (e.g., "user/repo")
            workflow: Workflow name
            conclusion: Workflow conclusion (success, failure, etc.)
            url: Optional workflow URL

        Returns:
            True if notification was queued successfully
        """
        try:
            # Select template based on conclusion
            if conclusion == "failure":
                template = settings.notification_template_failure
            elif conclusion == "success":
                template = settings.notification_template_success
            else:
                # Generic template for other conclusions
                template = (
                    f"GitHub Actions 通知：仓库 {{repo}}，工作流 {{workflow}} 状态为 {conclusion}"
                )

            # Format the message
            message = self._format_notification(
                template=template,
                repo=repo,
                workflow=workflow,
                conclusion=conclusion,
                url=url,
            )

            logger.info(f"Queueing notification: {message}")
            await self.queue.put(message)
            logger.info(f"Notification queued (queue size: {self.queue.qsize()})")

            return True

        except Exception as e:
            logger.error(f"Error queueing notification: {e}")
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

    def _should_use_speaker_tts(self, text: str) -> bool:
        """Determine if we should use speaker's built-in TTS.

        Args:
            text: Text to analyze

        Returns:
            True if should use speaker's built-in TTS, False otherwise
        """
        # If Piper Chinese voice is not configured, use speaker's TTS for Chinese
        if not settings.piper_voice_zh:
            return is_chinese(text)

        return False

    async def send_custom_notification(self, message: str) -> bool:
        """Send a custom notification message.

        Args:
            message: Custom message to send

        Returns:
            True if notification was queued successfully
        """
        try:
            logger.info(f"Queueing custom notification: {message}")
            await self.queue.put(message)
            logger.info(f"Custom notification queued (queue size: {self.queue.qsize()})")

            return True

        except Exception as e:
            logger.error(f"Error queueing custom notification: {e}")
            return False
