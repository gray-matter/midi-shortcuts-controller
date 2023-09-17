import asyncio
import logging
import pathlib
import re
import sys
from typing import List, Dict, Callable

import pulsectl_asyncio
import uinput
from pulsectl import PulseEventFacilityEnum, PulseEventTypeEnum
from pulsectl_asyncio import PulseAsync

from focus.browser_tab_focus import BrowserTabFocuser
from focus.no_focus import NoFocuser
from focus.window_focus import WindowFocuser
from input import WindowInput
from input.browser_input import BrowserInput
from input.pulse_sink_input import PulseSinkInput
from input.pulse_sinks import PulseSinks
from midi.midi_controller import MidiController
from sound.sound_player import SoundPlayer


def bootstrap_logging():
    console = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(name)s] %(asctime)s: %(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)
    logging.getLogger().setLevel(logging.INFO)


async def asyncify(callback: Callable):
    callback()


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
    ctrl = MidiController(re.compile('LPD8'))
    ctrl.connect()

    # Low-cost DJ mode
    cue_1 = WindowInput(WindowFocuser(re.compile("spotify.Spotify"), None), [uinput.KEY_1])
    cue_2 = WindowInput(WindowFocuser(re.compile("spotify.Spotify"), None), [uinput.KEY_2])
    cue_3 = WindowInput(WindowFocuser(re.compile("spotify.Spotify"), None), [uinput.KEY_3])
    cue_4 = WindowInput(WindowFocuser(re.compile("spotify.Spotify"), None), [uinput.KEY_4])

    rm_cue_1 = WindowInput(WindowFocuser(re.compile("spotify.Spotify"), None), [uinput.KEY_LEFTSHIFT, uinput.KEY_1])
    rm_cue_2 = WindowInput(WindowFocuser(re.compile("spotify.Spotify"), None), [uinput.KEY_LEFTSHIFT, uinput.KEY_2])
    rm_cue_3 = WindowInput(WindowFocuser(re.compile("spotify.Spotify"), None), [uinput.KEY_LEFTSHIFT, uinput.KEY_3])
    rm_cue_4 = WindowInput(WindowFocuser(re.compile("spotify.Spotify"), None), [uinput.KEY_LEFTSHIFT, uinput.KEY_4])

    ctrl.bind_note_on(1, lambda msg: cue_1.send())
    ctrl.bind_note_on(2, lambda msg: cue_2.send())
    ctrl.bind_note_on(3, lambda msg: cue_3.send())
    ctrl.bind_note_on(4, lambda msg: cue_4.send())

    ctrl.bind_control_change(1, lambda msg: rm_cue_1.send())
    ctrl.bind_control_change(2, lambda msg: rm_cue_2.send())
    ctrl.bind_control_change(3, lambda msg: rm_cue_3.send())
    ctrl.bind_control_change(4, lambda msg: rm_cue_4.send())

    drum_roll = SoundPlayer(pathlib.Path("media/drum-roll-short.wav"), True)
    cymbals = SoundPlayer(pathlib.Path("media/cymbals-crash-short.wav"))

    ctrl.bind_note_on(6, lambda msg: asyncify(drum_roll.toggle))
    ctrl.bind_note_on(7, lambda msg: asyncify(cymbals.play))

    # Work mode
    spatial_chat_mute = BrowserInput(BrowserTabFocuser(re.compile('firefox'), re.compile('Criteo SpatialChat')),
                                     WindowInput(WindowFocuser(re.compile('Navigator\\.firefox'),
                                                               re.compile('.*SpatialChat')),
                                                 [uinput.KEY_PAUSECD], [uinput.KEY_LEFTCTRL, uinput.KEY_E]))

    zoom_toggle_mute = WindowInput(WindowFocuser(re.compile("zoom"), re.compile("Zoom Meeting")),
                                   [uinput.KEY_PAUSECD], [uinput.KEY_LEFTALT, uinput.KEY_Q])

    ctrl.bind_note_on(21, lambda msg: zoom_toggle_mute.send())
    ctrl.bind_note_on(22, lambda msg: spatial_chat_mute.send())

    media_next = WindowInput(NoFocuser(), [uinput.KEY_NEXTSONG])
    media_previous = WindowInput(NoFocuser(), [uinput.KEY_PREVIOUSSONG])

    ctrl.bind_note_on(26, lambda msg: media_previous.send())
    ctrl.bind_note_on(27, lambda msg: media_next.send())
    ctrl.bind_note_on(27, lambda msg: media_next.send())

    ctrl.bind_control_change(36, lambda msg: sink_inputs['firefox-callback'].set_volume(msg.value / 127.))
    ctrl.bind_control_change(37, lambda msg: sink_inputs['chrome'].set_volume(msg.value / 127.))
    ctrl.bind_control_change(38, lambda msg: sink_inputs['zoom'].set_volume(msg.value / 127.))

    # Common
    play_pause = WindowInput(NoFocuser(), [uinput.KEY_PLAYPAUSE])

    for note_id in [5, 25, 45, 65]:
        ctrl.bind_note_on(note_id, lambda msg: play_pause.send())

    for cc_id in [11, 31, 51, 71]:
        ctrl.bind_control_change(cc_id, lambda msg: sinks.set_volume(msg.value / 127.))

    for cc_id in [15, 35]:
        ctrl.bind_control_change(cc_id, lambda msg: sink_inputs['spotify'].set_volume(msg.value / 127.))

    await ctrl.receive()


async def main():
    bootstrap_logging()

    async with pulsectl_asyncio.PulseAsync('midi-shortcuts-controller') as pulse_client:
        sink_inputs = {"spotify": PulseSinkInput(re.compile("spotify"), None, pulse_client),
                       "chrome": PulseSinkInput(re.compile("Chrom(e|ium)"), None, pulse_client),
                       "firefox-callback": PulseSinkInput(re.compile("Firefox"), "AudioCallbackDriver", pulse_client),
                       "zoom": PulseSinkInput(re.compile("ZOOM VoiceEngine"), "playStream", pulse_client)}
        sinks = PulseSinks(pulse_client)

        pulse_task = asyncio.create_task(pulse_loop(pulse_client, sink_inputs, sinks))
        inputs_task = asyncio.create_task(inputs_loop(sink_inputs, sinks))

        await pulse_task
        await inputs_task


asyncio.run(main())
