import logging
from typing import Any, Optional

LOGGER_KEY: Any
DEFAULT_LEVEL: Any
PY2: Any
text_type = str

class ColorFormatter(logging.Formatter):
    colors: Any = ...
    def format(self, record: Any): ...

class ClickHandler(logging.Handler):
    def emit(self, record: Any) -> None: ...

def basic_config(logger: Optional[Any] = ...): ...
