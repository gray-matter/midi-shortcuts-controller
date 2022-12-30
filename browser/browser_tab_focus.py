import logging
import re
import subprocess
from typing import Optional, Dict


class BrowserTabFocus:
    def __init__(self, browser_regex: re.Pattern, tab_regex: re.Pattern):
        self._browser_regex = browser_regex
        self._tab_regex = tab_regex

    def focus(self):
        self._find_browser()

    @staticmethod
    def _list_browsers() -> Dict[str, str]:
        p = subprocess.run(["bt", "clients"], text=True, capture_output=True)
        if p.returncode != 0:
            logging.warning("Could not list BroTab clients")
            return {}

        line_matcher = re.compile(f'\\^(.\\*)\\$')
        print(line_matcher)
        for line in p.stdout.split('\n'):
            print(line)
            matches = line_matcher.match(p.stdout)
            print(matches)
            print(matches.group(1))
            print(matches.group(2))

    def _find_browser(self) -> Optional:
        BrowserTabFocus._list_browsers()
