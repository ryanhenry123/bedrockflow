from enum import StrEnum, auto
from logging import getLevelNamesMapping


class LogLevel(StrEnum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

    def to_logging_level(self) -> int:
        return getLevelNamesMapping()[self.name]
