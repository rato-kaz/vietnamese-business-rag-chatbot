import asyncio
import signal
import sys
from contextlib import asynccontextmanager

from src.application.config import settings
from src.application.dependencies import initialize_dependencies, cleanup_dependencies
from src.infrastructure.logging.config import LoggingConfig
from src.infrastructure.logging.context import get_logger


@asynccontextmanager
async def application_lifespan():
    """Application lifespan manager."""
    logger = get_logger(__name__)
    
    try:
        # Setup logging
        LoggingConfig.setup_logging(
            log_level=settings.log_level,
            log_format=settings.log_format,
            log_dir=settings.log_dir,
            enable_console=settings.enable_console_logging,
            enable_file=settings.enable_file_logging,
            max_bytes=settings.log_max_bytes,
            backup_count=settings.log_backup_count
        )
        
        logger.info("Application starting up")
        
        # Initialize dependencies
        await initialize_dependencies()
        
        logger.info("Application startup completed")
        
        yield
        
    except Exception as e:
        logger.error(
            "Application startup failed",
            extra={"error": str(e)},
            exc_info=True
        )
        raise
    
    finally:
        # Cleanup
        logger.info("Application shutting down")
        await cleanup_dependencies()
        logger.info("Application shutdown completed")


class ChatbotApplication:
    """Main chatbot application."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._shutdown_event = asyncio.Event()
    
    async def start(self):
        """Start the application."""
        try:
            async with application_lifespan():
                self.logger.info("Chatbot application started")
                
                # Setup signal handlers
                self._setup_signal_handlers()
                
                # Wait for shutdown signal
                await self._shutdown_event.wait()
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(
                "Application error",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(
                "Received shutdown signal",
                extra={"signal": signum}
            )
            self._shutdown_event.set()
        
        # Setup handlers for SIGINT and SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def shutdown(self):
        """Trigger application shutdown."""
        self._shutdown_event.set()


async def main():
    """Main application entry point."""
    app = ChatbotApplication()
    await app.start()


if __name__ == "__main__":
    asyncio.run(main())