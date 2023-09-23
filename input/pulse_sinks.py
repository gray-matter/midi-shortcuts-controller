from pulsectl import PulseVolumeInfo
from pulsectl_asyncio import PulseAsync

from input.pulse_sinks_view import PulseSinksView


class PulseSinks:
    def __init__(self, sinks_view: PulseSinksView, pulse_client: PulseAsync):
        self._sinks_view = sinks_view
        self._pulse_client = pulse_client

    async def set_volume(self, percentage: float) -> None:
        """
        :param percentage: Between 0 and 1
        """
        for s in self._sinks_view.get():
            volume = PulseVolumeInfo(percentage, len(s.volume.values))
            await self._pulse_client.sink_volume_set(s.index, volume)
