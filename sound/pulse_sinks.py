import logging

from pulsectl import PulseVolumeInfo, PulseSinkInfo
from pulsectl_asyncio import PulseAsync

from sound.pulse_sinks_view import PulseSinksView


class SinksCountException(Exception):
    pass


class PulseSinks:
    def __init__(self, sinks_view: PulseSinksView, pulse_client: PulseAsync):
        self._sinks_view = sinks_view
        self._pulse_client = pulse_client

    async def set_volume(self, percentage: float) -> None:
        """
        :param percentage: Between 0 and 1
        """
        logging.debug(f'Setting volume to {percentage} for {self}')

        # FIXME: Warn when no result
        for s in self._sinks_view.get():
            volume = PulseVolumeInfo(percentage, len(s.volume.values))
            await self._pulse_client.sink_volume_set(s.index, volume)

    async def set_default(self) -> bool:
        try:
            raw_sink = self._get_raw_sink()
        except SinksCountException as e:
            logging.warning(f'Failed setting default sink: {e}')
            return False

        logging.info(f'Setting default sink to {raw_sink}')
        await self._pulse_client.sink_default_set(raw_sink)

        return True

    def _get_raw_sink(self) -> PulseSinkInfo:
        """
        :return:
        :raise SinksCountException
        """
        sinks = self._sinks_view.get()

        if len(sinks) > 1:
            raise SinksCountException(f'Too many sinks {len(sinks)} found ({self._sinks_view.description})')

        if len(sinks) == 0:
            raise SinksCountException(f'No sink found ({self._sinks_view.description})')

        return sinks[0]

    def __str__(self):
        return f"Sinks matching '{self._sinks_view.description}'"

    def __repr__(self):
        return f'PulseSinks(view={self._sinks_view.description})'
