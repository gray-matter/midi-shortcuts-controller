from typing import Callable, List

from pulsectl import PulseSinkInfo

from input.pulse_sinks_db import PulseSinksDb


class PulseSinksView:
    def __init__(self, matcher: Callable[[PulseSinkInfo], bool], pulse_sinks_db: PulseSinksDb):
        self._matcher = matcher
        self._pulse_sinks_db = pulse_sinks_db

    def get(self) -> List[PulseSinkInfo]:
        return list(filter(self._matcher, self._pulse_sinks_db.get()))
