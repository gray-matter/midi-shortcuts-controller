from typing import List, Iterable

import uinput
import logging


class WindowInput:
    def __init__(self, focuser, *inputs: List[int]):
        self._focuser = focuser
        self._inputs = inputs
        self._keyboard = uinput.Device(WindowInput._unique_inputs(inputs))

    async def send(self):
        if await self._focuser.focus():
            for virtual_input in self._inputs:
                self._keyboard.emit_combo(virtual_input, True)
                logging.debug(f'Sent {virtual_input}')

    @classmethod
    def _unique_inputs(cls: 'WindowInput', virtual_inputs: Iterable[List[int]]):
        result = set()
        for inputs in virtual_inputs:
            result.update(inputs)

        return result
