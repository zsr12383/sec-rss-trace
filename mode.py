from enum import Enum


class Mode(Enum):
    SC13 = 'sc13'
    MERGE = 'merge'

    def __str__(self) -> str:
        return self.value
