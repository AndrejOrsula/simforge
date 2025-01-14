import logging
import sys
from os import environ

from simforge.utils.tracing import with_logfire, with_rich

# Create a logger
logger = logging.getLogger("simforge")
logger.propagate = False

# Set the logger level
logger.setLevel(
    (environ.get("LOG_LEVEL") or environ.get("SF_LOG_LEVEL", "INFO")).upper()
)

# Set up console logging handlers (either rich or plain)
if with_rich():
    from rich.logging import RichHandler

    logger.addHandler(
        RichHandler(
            omit_repeated_times=False,
            rich_tracebacks=True,
            log_time_format="[%X]",
        )
    )
else:
    # Create a handler for logs below WARNING (DEBUG and INFO) to STDOUT
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)  # Allow DEBUG and INFO
    stdout_handler.addFilter(lambda record: record.levelno < logging.WARNING)

    # Create a handler for logs WARNING and above (WARNING, ERROR, CRITICAL) to STDERR
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)  # Allow WARNING and above

    # Define a formatter and set it for both handlers
    formatter = logging.Formatter(
        fmt="[{asctime}] {levelname:8s} {message}",
        datefmt="%H:%M:%S",
        style="{",
    )
    stdout_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)

# Set up Logfire logging handler
if with_logfire():
    from logfire import LogfireLoggingHandler

    logger.addHandler(LogfireLoggingHandler())


__all__ = [
    "logger",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
]

debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical
