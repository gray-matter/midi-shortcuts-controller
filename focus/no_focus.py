from focus.focuser import Focuser


class NoFocuser(Focuser):
    async def focus(self) -> bool:
        return True

    def __str__(self):
        return f'No focus'

    def __repr__(self):
        return f'NoFocus'
