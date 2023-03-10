import logging
from typing import List, Optional
from pulsectl import PulseVolumeInfo, PulseSinkInputInfo
from pulsectl_asyncio import PulseAsync


class PulseSinkInput:
    APP_NAME_KEY = 'application.name'
    MEDIA_NAME_KEY = 'media.name'

    def __init__(self, app_name: Optional[str], media_name: Optional[str], pulse: PulseAsync):
        self._app_name = app_name
        self._media_name = media_name
        self._sinks: List[PulseSinkInputInfo] = []
        self._pulse = pulse

    def _matches(self, source: PulseSinkInputInfo) -> bool:
        props = source.proplist
        return (self._app_name is None or PulseSinkInput.APP_NAME_KEY in props
                and props[PulseSinkInput.APP_NAME_KEY] == self._app_name) or \
               (self._app_name is None or PulseSinkInput.MEDIA_NAME_KEY in props
                and props[PulseSinkInput.MEDIA_NAME_KEY] == self._media_name)

    def refresh_sinks(self, input_list: List[PulseSinkInputInfo]):
        self._sinks = list(filter(self._matches, input_list))
        logging.debug(f'Found {len(self._sinks)} sink(s) for application {self._app_name}')

    async def set_volume(self, percentage: float):
        """
        :param percentage: Between 0 and 1
        """
        if len(self._sinks) == 0:
            logging.warning(f'Could not find sink for app "{self._app_name}"')

        for sink in self._sinks:
            volume_info = PulseVolumeInfo(percentage, len(sink.volume.values))
            await self._pulse.sink_input_volume_set(sink.index, volume_info)
            logging.debug(f'Set {sink.name} volume to {percentage}%')

    def __str__(self) -> str:
        return f'App_name: {self._app_name}'

    def __repr__(self) -> str:
        return f'PulseInput({self})'
