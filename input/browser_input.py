import logging

from browser.browser_tab_focus import BrowserTabFocus
from input import WindowInput


class BrowserInput:
    def __init__(self, browser_tab_focus: BrowserTabFocus, window_input: WindowInput):
        self._browser_tab_focus = browser_tab_focus
        self._window_input = window_input

    async def send(self):
        return await self._browser_tab_focus.focus() and await self._window_input.send()
