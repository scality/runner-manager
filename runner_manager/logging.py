import logging

format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, force=True, format=format)

log = logging.getLogger(__name__)
