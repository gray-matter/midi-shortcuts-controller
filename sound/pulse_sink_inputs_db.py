import logging
from typing import List, Callable, Coroutine

from pulsectl import PulseSinkInputInfo


class PulseSinkInputsDb:
    def __init__(self):
        self._sink_inputs = []
        self._change_callbacks = []

    async def refresh(self, sink_inputs: List[PulseSinkInputInfo]) -> None:
        logging.debug('Pulse sink inputs changed')

        self._sink_inputs = sink_inputs
        for cb in self._change_callbacks:
            await cb()

    def get(self) -> List[PulseSinkInputInfo]:
        return self._sink_inputs

    def register_to_change(self, callback: Callable[['PulseSinkInputsDb'], Coroutine]) -> None:
        self._change_callbacks.append(callback)
