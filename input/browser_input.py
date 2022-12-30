import logging
import re
from typing import List

import uinput


class BrowserInput:
    def __init__(self, browser_regex: re.Pattern, tab_regex: re.Pattern, virtual_input: List[int], only_first: bool = False):
        self._browser_regex = browser_regex
        self._tab_regex = tab_regex
        self._input = virtual_input
        self._only_first = only_first
        self._keyboard = uinput.Device(virtual_input)

    def send(self):
        target_tabs = []
        if len(target_tabs) == 0:
            logging.warning(f'Could not find {self._browser_regex} tab matching {self._tab_regex}')
            return

        if self._only_first:
            target_tabs = [target_tabs[0]]
