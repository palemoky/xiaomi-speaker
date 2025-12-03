"""Simple HTTP server for serving static audio files."""

import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread

from src.config import settings

logger = logging.getLogger(__name__)


class AudioFileHandler(SimpleHTTPRequestHandler):
    """Custom handler for serving audio files."""

    def __init__(self, *args, **kwargs):
        """Initialize handler with audio cache directory."""
        super().__init__(*args, directory=str(settings.audio_cache_dir), **kwargs)

    def log_message(self, format: str, *args) -> None:
        """Override to use Python logging instead of stderr."""
        logger.info(f"{self.address_string()} - {format % args}")


class StaticFileServer:
    """HTTP server for serving static audio files."""

    def __init__(self, host: str = None, port: int = None):
        """Initialize the static file server.

        Args:
            host: Server host (defaults to settings.static_server_host)
            port: Server port (defaults to settings.static_server_port)
        """
        self.host = host or settings.static_server_host
        self.port = port or settings.static_server_port
        self.server: HTTPServer = None
        self.thread: Thread = None

        # Ensure audio cache directory exists
        settings.ensure_audio_cache_dir()

    def start(self) -> None:
        """Start the static file server in a background thread."""
        if self.server:
            logger.warning("Static file server is already running")
            return

        try:
            self.server = HTTPServer(
                (self.host, self.port),
                AudioFileHandler,
            )

            logger.info(
                f"Starting static file server on {self.host}:{self.port}"
            )
            logger.info(f"Serving files from: {settings.audio_cache_dir}")

            # Run server in background thread
            self.thread = Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()

            logger.info("Static file server started successfully")

        except Exception as e:
            logger.error(f"Failed to start static file server: {e}")
            raise

    def stop(self) -> None:
        """Stop the static file server."""
        if self.server:
            logger.info("Stopping static file server...")
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            logger.info("Static file server stopped")

    def is_running(self) -> bool:
        """Check if the server is running.

        Returns:
            True if server is running
        """
        return self.server is not None and self.thread is not None and self.thread.is_alive()
