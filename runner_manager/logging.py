import logging

from runner_manager.dependencies import get_settings

settings = get_settings()

log_level = getattr(logging, settings.log_level, logging.INFO)
log = logging.getLogger(settings.name)
log.setLevel(log_level)

# console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)

# formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# add formatter to console handler
console_handler.setFormatter(formatter)
log.addHandler(console_handler)
