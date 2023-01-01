from typing import List

from pulsectl import PulseVolumeInfo, PulseSinkInfo
from pulsectl_asyncio import PulseAsync


class PulseSinks:
    def __init__(self, pulse_client: PulseAsync):
        self._pulse_client = pulse_client
        self._sinks = []

    def refresh(self, sinks_info: List[PulseSinkInfo]) -> None:
        self._sinks = list(filter(lambda sink: sink.state == 'running', sinks_info))

    async def set_volume(self, percentage: float):
        """
        Set volume for all running sinks.
        :param percentage: Between 0 and 1
        """
        for s in self._sinks:
            volume = PulseVolumeInfo(percentage, len(s.volume.values))
            await self._pulse_client.sink_volume_set(s.index, volume)
