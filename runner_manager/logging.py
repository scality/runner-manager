import logging

format = "%(levelname)s:     %(message)s"
logging.basicConfig(level=logging.INFO, force=True, format=format)

log = logging.getLogger(__name__)
