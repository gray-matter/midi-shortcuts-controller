from focus.focuser import Focuser


class NoFocuser(Focuser):
    async def focus(self) -> bool:
        return True
