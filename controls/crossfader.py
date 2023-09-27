import logging

from mido import Message

from sound.pulse_sinks import PulseSinks


class CrossFader:
    def __init__(self, left_sink: PulseSinks, right_sink: PulseSinks):
        self._left_sink = left_sink
        self._right_sink = right_sink

    async def update(self, msg: Message) -> None:
        value = msg.value
        logging.debug(f'Crossfader between {self._left_sink} and {self._right_sink}: {value}')

        mid_value = 127 / 2
        left_value = max((value - mid_value) * 2 / 100, 0)
        right_value = max((mid_value - value) * 2 / 100, 0)

        await self._left_sink.set_volume(right_value)
        await self._right_sink.set_volume(left_value)

        if value > mid_value:
            await self._right_sink.set_default()
        else:
            await self._left_sink.set_default()
