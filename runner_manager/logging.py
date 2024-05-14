import json
import logging


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {
                "time": self.formatTime(record),
                "name": record.name,
                "level": record.levelname,
                "message": record.getMessage(),
            }
        )


handler = logging.StreamHandler()
formatter = JsonFormatter()
handler.setFormatter(formatter)

logging.basicConfig(level=logging.INFO, handlers=[handler])
log = logging.getLogger(__name__)
