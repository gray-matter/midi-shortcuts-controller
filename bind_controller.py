import asyncio
import logging
import re
import sys
from typing import List, Dict

import pulsectl_asyncio
import uinput
from pulsectl import PulseEventFacilityEnum, PulseEventTypeEnum
from pulsectl_asyncio import PulseAsync

from browser.browser_tab_focus import BrowserTabFocus
from input import WindowInput
from input.pulse_sink_input import PulseSinkInput
from input.pulse_sinks import PulseSinks
from midi.MidiController import MidiController


def bootstrap_logging():
    console = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(name)s] %(asctime)s: %(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)
    logging.getLogger().setLevel(logging.INFO)


async def refresh_sink_inputs(knobs: List[PulseSinkInput], pulse_client: PulseAsync):
    input_list = await pulse_client.sink_input_list()

    for knob in knobs:
        logging.debug(f'Refresh {knob}')
        knob.refresh_sinks(input_list)


async def refresh_sinks(sinks: PulseSinks, pulse_client: PulseAsync):
    sinks.refresh(await pulse_client.sink_list())


async def pulse_loop(pulse_client: PulseAsync, sink_inputs: Dict[str, PulseSinkInput],
                     sinks: PulseSinks):
    await refresh_sink_inputs(list(sink_inputs.values()), pulse_client)
    await refresh_sinks(sinks, pulse_client)

    async for ev in pulse_client.subscribe_events('all'):
        if ev.facility in [PulseEventFacilityEnum.sink_input] and \
                ev.t in [PulseEventTypeEnum.new, PulseEventTypeEnum.remove]:
            await refresh_sink_inputs(list(sink_inputs.values()), pulse_client)

        if ev.facility in [PulseEventFacilityEnum.sink] and \
                ev.t in [PulseEventTypeEnum.new, PulseEventTypeEnum.remove]:
            await refresh_sinks(sinks, pulse_client)


async def inputs_loop(sink_inputs: Dict[str, PulseSinkInput], sinks: PulseSinks):
    wi_1 = WindowInput(re.compile("spotify.Spotify"), None, [uinput.KEY_1])
    wi_2 = WindowInput(re.compile("spotify.Spotify"), None, [uinput.KEY_2])
    wi_3 = WindowInput(re.compile("spotify.Spotify"), None, [uinput.KEY_3])
    wi_4 = WindowInput(re.compile("spotify.Spotify"), None, [uinput.KEY_4])

    wis_1 = WindowInput(re.compile("spotify.Spotify"), None, [uinput.KEY_LEFTSHIFT, uinput.KEY_1])
    wis_2 = WindowInput(re.compile("spotify.Spotify"), None, [uinput.KEY_LEFTSHIFT, uinput.KEY_2])
    wis_3 = WindowInput(re.compile("spotify.Spotify"), None, [uinput.KEY_LEFTSHIFT, uinput.KEY_3])
    wis_4 = WindowInput(re.compile("spotify.Spotify"), None, [uinput.KEY_LEFTSHIFT, uinput.KEY_4])

    bi = BrowserTabFocus(re.compile('firefox'), re.compile('PulseAudio.*'))

    zoom_toggle_mute = WindowInput(re.compile("zoom"), re.compile("Zoom Meeting"),
                                   [uinput.KEY_LEFTALT, uinput.KEY_Q])

    ctrl = MidiController(re.compile('LPD8'))
    ctrl.connect()

    ctrl.bind_note_on(1, lambda msg: wi_1.send())
    ctrl.bind_note_on(2, lambda msg: wi_2.send())
    ctrl.bind_note_on(3, lambda msg: wi_3.send())
    ctrl.bind_note_on(4, lambda msg: wi_4.send())

    ctrl.bind_note_on(21, lambda msg: zoom_toggle_mute.send())
    ctrl.bind_note_on(22, lambda msg: bi.focus())

    ctrl.bind_control_change(1, lambda msg: wis_1.send())
    ctrl.bind_control_change(2, lambda msg: wis_2.send())
    ctrl.bind_control_change(3, lambda msg: wis_3.send())
    ctrl.bind_control_change(4, lambda msg: wis_4.send())

    ctrl.bind_control_change(11, lambda msg: sinks.set_volume(msg.value / 127.))

    ctrl.bind_control_change(15, lambda msg: sink_inputs['spotify'].set_volume(msg.value / 127.))
    ctrl.bind_control_change(16, lambda msg: sink_inputs['firefox-callback'].set_volume(msg.value / 127.))

    await ctrl.receive()


async def main():
    bootstrap_logging()

    async with pulsectl_asyncio.PulseAsync('midi-shortcuts-controller') as pulse_client:
        sink_inputs = {"spotify": PulseSinkInput("spotify", None, pulse_client),
                       "firefox-callback": PulseSinkInput("Firefox", "AudioCallbackDriver", pulse_client)}
        sinks = PulseSinks(pulse_client)

        pulse_task = asyncio.create_task(pulse_loop(pulse_client, sink_inputs, sinks))
        inputs_task = asyncio.create_task(inputs_loop(sink_inputs, sinks))

        await pulse_task
        await inputs_task


asyncio.run(main())
