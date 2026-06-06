import asyncio
import signal
import sys

import structlog

from src.config import load_config
from src.scheduler import Monitor, create_scheduler


def main():
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logger = structlog.get_logger()

    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    logger.info("Loading config", path=config_path)

    try:
        config = load_config(config_path)
    except Exception as e:
        logger.error("Failed to load config", error=str(e))
        sys.exit(1)

    monitor = Monitor(config)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        await monitor.start()

        if "--once" in sys.argv:
            await monitor.tick()
            await monitor.shutdown()
            logger.info("Once-off run complete")
            return

        scheduler = create_scheduler(monitor)
        scheduler.start()

        # Run first tick immediately
        await monitor.tick()

        # Wait forever until signal
        stop_event = asyncio.Event()

        def handle_signal(sig, frame):
            logger.info("Received signal", signal=sig)
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda s=sig: handle_signal(s, None))
            except NotImplementedError:
                # Windows does not support add_signal_handler
                signal.signal(sig, handle_signal)

        await stop_event.wait()

        scheduler.shutdown()
        await monitor.shutdown()

    try:
        loop.run_until_complete(run())
    finally:
        loop.close()
        logger.info("Exited")


if __name__ == "__main__":
    main()
