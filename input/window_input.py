from typing import List

import uinput
import logging


class WindowInput:
    def __init__(self, focuser, virtual_input: List[int]):
        self._focuser = focuser
        self._input = virtual_input
        self._keyboard = uinput.Device(virtual_input)

    async def send(self):
        if await self._focuser.focus():
            self._keyboard.emit_combo(self._input, True)
            logging.debug(f'Sent {self._input}')
