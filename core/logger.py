import logging


logging.basicConfig(
    level=logging.DEBUG, format="%(name)s - %(levelname)s| %(message)s"
)
mylogger = logging.getLogger(__name__)
