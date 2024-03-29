import logging

from focus.browser_tab_focus import BrowserTabFocuser
from input import WindowInput


class BrowserInput:
    def __init__(self, browser_tab_focus: BrowserTabFocuser, window_input: WindowInput):
        self._browser_tab_focus = browser_tab_focus
        self._window_input = window_input

    async def send(self):
        return await self._browser_tab_focus.focus() and await self._window_input.send()
