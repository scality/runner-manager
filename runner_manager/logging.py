import logging

from runner_manager.models.settings import Settings

settings = Settings()

log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
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
