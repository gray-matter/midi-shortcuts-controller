from pulsectl_asyncio import PulseAsync


class PulseVolumeInput:
    def __init__(self, pulse: PulseAsync):
        self._pulse = pulse

    async def set_volume(self, percentage: float):
        self._pulse.volume_set()
