import pytest
import logging
from ham import set_debug, set_verbose


def test_logger_tags():
    # create a new ham logger
    logger = logging.getLogger("ham.tests.core")

    # no - ops
    logger.info("This is a test message")
    logger.debug("This is a debug message")
    # toggle
    set_verbose(True)
    # op
    logger.info("This is a test message")
    # no-op
    logger.debug("This is a debug message")
    set_debug(True)
    # both ops
    logger.info("This is a test message")
    logger.debug("This is a debug message")


if __name__ == "__main__":
    test_logger_tags()
