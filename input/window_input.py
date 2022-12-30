import asyncio
import time
from typing import List

import uinput
from wmctrl import Window
import logging


class WindowInput:
    # TODO: Come back to previous window?
    def __init__(self, window_class: str, virtual_input: List[int], only_first: bool = False):
        self._window_class = window_class
        self._input = virtual_input
        self._only_first = only_first
        self._keyboard = uinput.Device(virtual_input)

    async def send(self):
        target_windows = list(filter(lambda w: w.wm_class == self._window_class, Window.list()))

        if len(target_windows) == 0:
            logging.warning(f'Could not find window with class {self._window_class}')
            return

        if self._only_first:
            target_windows = [target_windows[0]]

        for window in target_windows:
            window.activate()

            timeout = 5
            timeout_start = time.time()
            activated = False

            while time.time() < timeout_start + timeout:
                if Window.get_active() == window:
                    activated = True
                    break
                await asyncio.sleep(0.1)

            await asyncio.sleep(0.1)
            if activated:
                self._keyboard.emit_combo(self._input, True)
                logging.info(f'Sent {self._input} to {window.wm_name} ({window.wm_class})')
            else:
                logging.warning(f'Could not activate {window.wm_name} ({window.wm_class}) within {timeout}s')
