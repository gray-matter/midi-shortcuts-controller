import asyncio
import re
import time
from typing import List, Optional

import uinput
from wmctrl import Window
import logging


class WindowInput:
    def __init__(self, window_class_pattern: re.Pattern, window_name_pattern: Optional[re.Pattern], virtual_input: List[int],
                 only_first: bool = True):
        self._window_class_pattern = window_class_pattern
        self._window_name_pattern = window_name_pattern
        self._input = virtual_input
        self._only_first = only_first
        self._keyboard = uinput.Device(virtual_input)

    async def send(self):
        def is_target_window(w: Window):
            return (self._window_class_pattern is None or self._window_class_pattern.search(w.wm_class)) and \
                (self._window_name_pattern is None or self._window_name_pattern.search(w.wm_name))

        target_windows = list(filter(is_target_window, Window.list()))

        if len(target_windows) == 0:
            logging.warning(f'Could not find window with class {self._window_class_pattern.pattern} and name '
                            f'{self._window_name_pattern.pattern}')
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
                logging.debug(f'Sent {self._input} to {window.wm_name} ({window.wm_class})')
            else:
                logging.warning(f'Could not activate {window.wm_name} ({window.wm_class}) within {timeout}s')
