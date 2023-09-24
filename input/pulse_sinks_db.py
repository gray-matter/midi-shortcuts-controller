from typing import List

from pulsectl import PulseSinkInfo


class PulseSinksDb:
    def __init__(self):
        self._sinks = []

    def refresh(self, sinks_info: List[PulseSinkInfo]) -> None:
        self._sinks = sinks_info

    def get(self) -> List[PulseSinkInfo]:
        return self._sinks
