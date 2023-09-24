from typing import List

from pulsectl import PulseSinkInputInfo


class PulseSinkInputsDb:
    def __init__(self):
        self._sink_inputs = []

    def refresh(self, sink_inputs: List[PulseSinkInputInfo]) -> None:
        self._sink_inputs = sink_inputs

    def get(self) -> List[PulseSinkInputInfo]:
        return self._sink_inputs
