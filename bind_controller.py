import asyncio
import logging
import re
import sys
from typing import List, Dict, Awaitable, Coroutine, Any, Callable

import mido
import pulsectl_asyncio
import uinput
from pulsectl import PulseEventFacilityEnum, PulseEventTypeEnum
from pulsectl_asyncio import PulseAsync

from input import WindowInput
from input.pulse_input import PulseInput
from midi.MidController import MidiController


def bootstrap_logging():
    console = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(name)s] %(asctime)s: %(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)
    logging.getLogger().setLevel(logging.INFO)


async def refresh_knobs(knobs: List[PulseInput], pulse_client: PulseAsync):
    input_list = await pulse_client.sink_input_list()

    for knob in knobs:
        logging.info(f'Refresh {knob}')
        knob.refresh_sinks(input_list)


async def pulse_loop(pulse_client: PulseAsync, knobs: Dict[str, PulseInput]):
    await refresh_knobs(list(knobs.values()), pulse_client)

    async for ev in pulse_client.subscribe_events('all'):
        if ev.facility in [PulseEventFacilityEnum.sink_input] and \
                ev.t in [PulseEventTypeEnum.new, PulseEventTypeEnum.remove]:
            await refresh_knobs(list(knobs.values()), pulse_client)


async def inputs_loop(knobs: Dict[str, PulseInput]):
    wi_1 = WindowInput("spotify.Spotify", [uinput.KEY_1])
    ctrl = MidiController(re.compile('LPD8'))
    ctrl.connect()
    ctrl.bind_note_on(38, lambda msg: wi_1.send())
    ctrl.bind_control_change(0, lambda msg: knobs['spotify'].set_volume(msg.value / 100.))

    await ctrl.receive()


async def main():
    bootstrap_logging()

    async with pulsectl_asyncio.PulseAsync('pad') as pulse_client:
        knobs = {"spotify": PulseInput("spotify", pulse_client)}

        pulse_task = asyncio.create_task(pulse_loop(pulse_client, knobs))
        inputs_task = asyncio.create_task(inputs_loop(knobs))

        await pulse_task
        await inputs_task


asyncio.run(main())
