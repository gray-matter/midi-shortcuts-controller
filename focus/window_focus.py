import asyncio
import re
from datetime import timedelta
import logging
import time
from typing import Optional

from wmctrl import Window


class WindowFocus:
    def __init__(self, window_class_pattern: re.Pattern, window_name_pattern: Optional[re.Pattern],
                 time_to_focus: timedelta = timedelta(seconds=5)):
        self._window_class_pattern = window_class_pattern
        self._window_name_pattern = window_name_pattern
        self._time_to_focus = time_to_focus

    async def focus(self) -> bool:
        search_description = f'class {self._window_class_pattern} and name {self._window_name_pattern}'

        def is_target_window(w: Window):
            return (self._window_class_pattern is None or self._window_class_pattern.search(w.wm_class)) and \
                (self._window_name_pattern is None or self._window_name_pattern.search(w.wm_name))

        target_windows = list(filter(is_target_window, Window.list()))

        if len(target_windows) == 0:
            logging.warning(f'Could not find window with {search_description}')
            return False

        if len(target_windows) > 1:
            logging.warning(f'More than one window matched {search_description}')

        target_window = target_windows[0]

        target_window.activate()
        timeout_start = time.time()

        while time.time() - timeout_start < self._time_to_focus.seconds:
            if Window.get_active() == target_window:
                await asyncio.sleep(0.1)
                return True
            await asyncio.sleep(0.1)

        logging.warning(f'Could not activate window with {search_description} within {timeout}s')
        return False
