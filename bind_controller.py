import asyncio
import logging
import pathlib
import re
import sys
from typing import Callable

import pulsectl_asyncio
import pyudev
import uinput
from mido import Message
from pulsectl import PulseEventFacilityEnum, PulseEventTypeEnum
from pulsectl_asyncio import PulseAsync

from controls.crossfader import CrossFader
from focus.browser_tab_focus import BrowserTabFocuser
from focus.no_focus import NoFocuser
from focus.window_focus import WindowFocuser
from input import WindowInput
from input.browser_input import BrowserInput
from midi.controller_mapping import ControllerMapping
from midi.midi_controller import MidiController
from midi.program import Program
from sound.pulse_sink_input import PulseSinkInput
from sound.pulse_sink_inputs_db import PulseSinkInputsDb
from sound.pulse_sinks import PulseSinks
from sound.pulse_sinks_db import PulseSinksDb
from sound.pulse_sinks_view import PulseSinksView
from sound.sound_player import SoundPlayer


def bootstrap_logging():
    console = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(name)s] %(asctime)s: %(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)
    logging.getLogger().setLevel(logging.INFO)


async def asyncify(callback: Callable):
    callback()


async def refresh_sink_inputs(sink_inputs_db: PulseSinkInputsDb, pulse_client: PulseAsync):
    await sink_inputs_db.refresh(await pulse_client.sink_input_list())


async def refresh_sinks(sinks_db: PulseSinksDb, pulse_client: PulseAsync):
    sinks_db.refresh(await pulse_client.sink_list())


async def pulse_loop(pulse_client: PulseAsync, sinks_db: PulseSinksDb, sink_inputs_db: PulseSinkInputsDb):
    await refresh_sink_inputs(sink_inputs_db, pulse_client)
    await refresh_sinks(sinks_db, pulse_client)

    async for ev in pulse_client.subscribe_events('all'):
        if ev.facility in [PulseEventFacilityEnum.sink_input] and \
                ev.t in [PulseEventTypeEnum.new, PulseEventTypeEnum.remove]:
            await refresh_sink_inputs(sink_inputs_db, pulse_client)

        if ev.facility in [PulseEventFacilityEnum.sink] and \
                ev.t in [PulseEventTypeEnum.new, PulseEventTypeEnum.remove]:
            await refresh_sinks(sinks_db, pulse_client)


def bind_common(ctrl: MidiController, program: Program) -> None:
    play_pause = WindowInput(NoFocuser(), [uinput.KEY_PLAYPAUSE])
    ctrl.bind_note_on(program.get_pad(5), lambda msg: play_pause.send())


def bind_dj_mode(ctrl: MidiController, program: Program, sinks_db: PulseSinksDb, sink_inputs_db: PulseSinkInputsDb,
                 pulse_client: PulseAsync) -> None:
    spotify_focuser = WindowFocuser(re.compile("spotify.Spotify"), None)

    cue_1 = WindowInput(spotify_focuser, [uinput.KEY_1])
    cue_2 = WindowInput(spotify_focuser, [uinput.KEY_2])
    cue_3 = WindowInput(spotify_focuser, [uinput.KEY_3])
    cue_4 = WindowInput(spotify_focuser, [uinput.KEY_4])

    rm_cue_1 = WindowInput(spotify_focuser, [uinput.KEY_LEFTSHIFT, uinput.KEY_1])
    rm_cue_2 = WindowInput(spotify_focuser, [uinput.KEY_LEFTSHIFT, uinput.KEY_2])
    rm_cue_3 = WindowInput(spotify_focuser, [uinput.KEY_LEFTSHIFT, uinput.KEY_3])
    rm_cue_4 = WindowInput(spotify_focuser, [uinput.KEY_LEFTSHIFT, uinput.KEY_4])

    ctrl.bind_note_on(program.get_pad(1), lambda msg: cue_1.send())
    ctrl.bind_note_on(program.get_pad(2), lambda msg: cue_2.send())
    ctrl.bind_note_on(program.get_pad(3), lambda msg: cue_3.send())
    ctrl.bind_note_on(program.get_pad(4), lambda msg: cue_4.send())

    async def send_if_not_0(msg: Message, window_input: WindowInput):
        if msg.value > 0:
            await window_input.send()

    ctrl.bind_control_change(program.get_pad(1), lambda msg: send_if_not_0(msg, rm_cue_1))
    ctrl.bind_control_change(program.get_pad(2), lambda msg: send_if_not_0(msg, rm_cue_2))
    ctrl.bind_control_change(program.get_pad(3), lambda msg: send_if_not_0(msg, rm_cue_3))
    ctrl.bind_control_change(program.get_pad(4), lambda msg: send_if_not_0(msg, rm_cue_4))

    drum_roll = SoundPlayer(pathlib.Path("media/drum-roll-short.wav"), True)
    cymbals = SoundPlayer(pathlib.Path("media/cymbals-crash-short.wav"))
    wah_wah = SoundPlayer(pathlib.Path("media/wah-wah.wav"))

    ctrl.bind_note_on(program.get_pad(6), lambda msg: asyncify(drum_roll.toggle))
    ctrl.bind_note_on(program.get_pad(7), lambda msg: asyncify(cymbals.play))
    ctrl.bind_note_on(program.get_pad(8), lambda msg: asyncify(wah_wah.play))

    headset_re = re.compile('W[FH]-1000XM')
    headset_sink = PulseSinks(PulseSinksView(lambda sink: headset_re.match(sink.description) is not None, sinks_db,
                                             'Sony BT headsets'), pulse_client)
    speaker_sink = PulseSinks(PulseSinksView(lambda sink: 'Speaker + Headphones' in sink.description,
                                             sinks_db, 'Speaker or jack attachment'), pulse_client)

    spotify_sink_input = PulseSinkInput(re.compile("(spotify|ALSA plug-in)"), None, sink_inputs_db, pulse_client)
    sink_inputs_db.register_to_change(spotify_sink_input.update)

    crossfader = CrossFader(headset_sink, speaker_sink)
    ctrl.bind_control_change(program.get_knob(1), crossfader.update)
    ctrl.bind_control_change(program.get_knob(5), lambda msg: spotify_sink_input.set_volume(msg.value / 127.))

    bind_common(ctrl, program)


def bind_work_mode(ctrl: MidiController, program: Program, sinks_db: PulseSinksDb,
                   sink_inputs_db: PulseSinkInputsDb, pulse_client: PulseAsync) -> None:
    spatial_chat_mute = BrowserInput(BrowserTabFocuser(re.compile('firefox'), re.compile('Criteo SpatialChat')),
                                     WindowInput(WindowFocuser(re.compile('Navigator\\.firefox'),
                                                               re.compile('.*SpatialChat')),
                                                 [uinput.KEY_PAUSECD], [uinput.KEY_LEFTCTRL, uinput.KEY_E]))

    # TODO: Match small Zoom window
    zoom_toggle_mute = WindowInput(WindowFocuser(re.compile("zoom"), re.compile("Zoom Meeting")),
                                   [uinput.KEY_PAUSECD], [uinput.KEY_LEFTALT, uinput.KEY_Q])

    teams_mute = BrowserInput(BrowserTabFocuser(re.compile('firefox'), re.compile('Microsoft Teams')),
                              WindowInput(WindowFocuser(re.compile('Navigator\\.firefox'),
                                                        re.compile('.*Microsoft Teams')),
                                          [uinput.KEY_PAUSECD],
                                          [uinput.KEY_LEFTCTRL, uinput.KEY_LEFTSHIFT, uinput.KEY_SEMICOLON]))

    ctrl.bind_note_on(program.get_pad(1), lambda msg: zoom_toggle_mute.send())
    ctrl.bind_note_on(program.get_pad(2), lambda msg: spatial_chat_mute.send())
    ctrl.bind_note_on(program.get_pad(3), lambda msg: teams_mute.send())

    media_next = WindowInput(NoFocuser(), [uinput.KEY_NEXTSONG])
    media_previous = WindowInput(NoFocuser(), [uinput.KEY_PREVIOUSSONG])

    ctrl.bind_note_on(program.get_pad(6), lambda msg: media_previous.send())
    ctrl.bind_note_on(program.get_pad(7), lambda msg: media_next.send())

    firefox_sink_input = PulseSinkInput(re.compile("Firefox"), None, sink_inputs_db,
                                        pulse_client)
    ctrl.bind_control_change(program.get_knob(6), lambda msg: firefox_sink_input.set_volume(msg.value / 127.))

    chrome_sink_input = PulseSinkInput(re.compile("Chrom(e|ium)"), None, sink_inputs_db, pulse_client)
    ctrl.bind_control_change(program.get_knob(7), lambda msg: chrome_sink_input.set_volume(msg.value / 127.))

    zoom_sink_input = PulseSinkInput(re.compile("ZOOM VoiceEngine"), re.compile("playStream"), sink_inputs_db,
                                     pulse_client)
    ctrl.bind_control_change(program.get_knob(8), lambda msg: zoom_sink_input.set_volume(msg.value / 127.))

    running_sinks = PulseSinks(PulseSinksView(lambda sink: sink.state == 'running', sinks_db,
                                              'All running sinks'), pulse_client)
    ctrl.bind_control_change(program.get_knob(1), lambda msg: running_sinks.set_volume(msg.value / 127.))

    spotify_sink_input = PulseSinkInput(re.compile("spotify"), None, sink_inputs_db, pulse_client)
    ctrl.bind_control_change(program.get_knob(5), lambda msg: spotify_sink_input.set_volume(msg.value / 127.))
    sink_inputs_db.register_to_change(spotify_sink_input.update)

    bind_common(ctrl, program)


def watch_usb_events(ctrl: MidiController):
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='usb')

    observer = pyudev.MonitorObserver(monitor, lambda evt, _: evt == 'bind' and ctrl.connect())
    observer.start()


async def inputs_loop(pulse_client: PulseAsync, sinks_db: PulseSinksDb, sink_inputs_db: PulseSinkInputsDb) -> None:
    ctrl = MidiController(re.compile('LPD8'))
    ctrl.connect()

    mapping = ControllerMapping(4)
    mapping.map(1, Program(list(range(1, 9)), list(range(11, 19))))
    mapping.map(2, Program(list(range(21, 29)), list(range(31, 39))))
    mapping.map(3, Program(list(range(41, 49)), list(range(51, 59))))
    mapping.map(4, Program(list(range(61, 69)), list(range(71, 79))))

    bind_dj_mode(ctrl, mapping.get(1), sinks_db, sink_inputs_db, pulse_client)
    bind_work_mode(ctrl, mapping.get(2), sinks_db, sink_inputs_db, pulse_client)

    watch_usb_events(ctrl)

    await ctrl.receive()


async def main():
    bootstrap_logging()

    pulse_client: PulseAsync
    async with pulsectl_asyncio.PulseAsync('midi-shortcuts-controller') as pulse_client:
        sink_inputs_db = PulseSinkInputsDb()
        sinks_db = PulseSinksDb()

        pulse_task = asyncio.create_task(pulse_loop(pulse_client, sinks_db, sink_inputs_db))
        inputs_task = asyncio.create_task(inputs_loop(pulse_client, sinks_db, sink_inputs_db))

        await pulse_task
        await inputs_task


asyncio.run(main())
