import logging
import re
from typing import List, Optional
from pulsectl import PulseVolumeInfo, PulseSinkInputInfo
from pulsectl_asyncio import PulseAsync

from sound.pulse_sink_inputs_db import PulseSinkInputsDb
from sound.pulse_sinks import PulseSinks, SinksCountException


class PulseSinkInput:
    APP_NAME_KEY = 'application.name'
    MEDIA_NAME_KEY = 'media.name'

    def __init__(self, app_name_pattern: Optional[re.Pattern], media_name_pattern: Optional[re.Pattern],
                 sink_inputs_db: PulseSinkInputsDb, pulse_client: PulseAsync):
        self._app_name_pattern = app_name_pattern
        self._media_name_pattern = media_name_pattern
        self._sink_inputs_db = sink_inputs_db
        self._pulse_client = pulse_client
        self._current_volume: Optional[float] = None

    async def set_volume(self, percentage: float):
        """
        :param percentage: Between 0 and 1
        """
        logging.debug(f'Setting volume for {self} to {percentage * 100}%')
        self._current_volume = percentage
        await self._set_volume(percentage)

    async def move(self, sink: PulseSinks) -> bool:
        try:
            sink_index = sink.get_index()
        except SinksCountException as e:
            logging.warning(f'Failed to move {self}: {e}')
            return False

        sink_inputs = self._get_matching_sink_inputs()
        logging.debug(f'Moving sink inputs {sink_inputs} to sink {sink_index}')

        for sink_input in sink_inputs:
            await self._pulse_client.sink_input_move(sink_input.index, sink_index)
            return True

    async def update(self) -> None:
        logging.debug(f'Updating {self} (current volume = {self._current_volume})')
        if self._current_volume is not None:
            logging.info(f'Setting volume for {self} to {self._current_volume * 100}%')
            await self._set_volume(self._current_volume)

    def _matches(self, source: PulseSinkInputInfo) -> bool:
        props = source.proplist
        return (self._app_name_pattern is None or PulseSinkInput.APP_NAME_KEY in props
                and self._app_name_pattern.search(props[PulseSinkInput.APP_NAME_KEY])) and \
            (self._media_name_pattern is None or PulseSinkInput.MEDIA_NAME_KEY in props
             and self._media_name_pattern.search(props[PulseSinkInput.MEDIA_NAME_KEY]))

    async def _set_volume(self, percentage: float):
        sink_inputs = self._get_matching_sink_inputs()

        if len(sink_inputs) == 0:
            logging.warning(f'Could not find sink for {self}')

        for sink in sink_inputs:
            volume_info = PulseVolumeInfo(percentage, len(sink.volume.values))
            await self._pulse_client.sink_input_volume_set(sink.index, volume_info)
            logging.debug(f'Set {sink.name} volume to {percentage * 100}%')

    def _get_matching_sink_inputs(self) -> List[PulseSinkInputInfo]:
        return list(filter(self._matches, self._sink_inputs_db.get()))

    def __str__(self) -> str:
        return f'App_name: {self._app_name_pattern}, media name: {self._media_name_pattern}'

    def __repr__(self) -> str:
        return f'PulseInput({self})'
