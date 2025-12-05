"""Main application entry point."""

import asyncio
import logging
import signal
import sys

import uvicorn

from src.config import settings
from src.server import app
from src.static_server import StaticFileServer

logger = logging.getLogger(__name__)

# Global server instances
static_server: StaticFileServer | None = None
shutdown_event = asyncio.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info(f"Received signal {signum}, initiating shutdown...")
    shutdown_event.set()


def main():
    """Main application entry point."""
    global static_server

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start static file server
        logger.info("Starting static file server...")
        static_server = StaticFileServer()
        static_server.start()

        # Start FastAPI webhook server
        logger.info("Starting webhook server...")
        logger.info(f"Webhook server: http://{settings.server_host}:{settings.server_port}")
        logger.info(
            f"Static server: http://{settings.static_server_host}:{settings.static_server_port}"
        )

        # Run uvicorn server
        config = uvicorn.Config(
            app,
            host=settings.server_host,
            port=settings.server_port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        server.run()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        if static_server:
            logger.info("Stopping static file server...")
            static_server.stop()
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()
