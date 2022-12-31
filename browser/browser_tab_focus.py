import logging
import re
import subprocess
from typing import Optional, Dict, List


class BrowserTabFocus:
    def __init__(self, browser_regex: re.Pattern, tab_regex: re.Pattern):
        self._browser_regex = browser_regex
        self._tab_regex = tab_regex

    async def focus(self):
        """
        Focus first tab in first tab matching the regex
        """
        browser_id = self._find_browser()
        if browser_id is None:
            logging.warning(f'Could not find browser matching {self._browser_regex}')
            return

        tab_id = self._find_tab(browser_id)
        if tab_id is None:
            logging.warning(f'Could not find tab matching {self._tab_regex}')
            return

        if self._focus_tab(tab_id):
            logging.info(f'Focused {tab_id}')

    @staticmethod
    def _list_bt_objects(command: List[str], line_matcher: re) -> Optional[Dict[str, str]]:
        p = subprocess.run(command, text=True, capture_output=True)
        if p.returncode != 0:
            return None

        objects = {}
        for line in p.stdout.split('\n'):
            matches = line_matcher.match(line)
            if matches:
                objects[matches.group(1)] = matches.group(2)

        return objects

    @staticmethod
    def _list_browsers() -> Optional[Dict[str, str]]:
        return BrowserTabFocus._list_bt_objects(["bt", "clients"], re.compile('^([^.]+)\\..*\\s+(\\S+)$'))

    @staticmethod
    def _list_tabs(browser_id: str) -> Optional[Dict[str, str]]:
        return BrowserTabFocus._list_bt_objects(["bt", "list"], re.compile(f'(^{browser_id}\\.[^\t]+)\t([^\t]+)'))

    def _find_browser(self) -> Optional[str]:
        for browser_id, browser_name in BrowserTabFocus._list_browsers().items():
            if self._browser_regex.match(browser_name):
                return browser_id

        return None

    def _find_tab(self, browser_id: str) -> Optional[str]:
        for tab_id, tab_name in BrowserTabFocus._list_tabs(browser_id).items():
            if self._tab_regex.match(tab_name):
                return tab_id

        return None

    @staticmethod
    def _focus_tab(tab_id: str) -> bool:
        p = subprocess.run(['bt', 'activate', tab_id])
        if p.returncode != 0:
            logging.warning(f'Failed to activate {tab_id}')
            return False

        return True
