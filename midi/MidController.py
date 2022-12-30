import asyncio
import logging
import re
from collections import defaultdict
from typing import Optional, List, Callable, Awaitable

import mido


class MidiController:
    CONTROL_CHANGE = 'control_change'
    NOTE_ON = 'note_on'
    NOTE_OFF = 'note_on'

    def __init__(self, name_regex: re.Pattern):
        self._controls_bindings = defaultdict(list)
        self._outport = None
        self._inport = None
        self._midi_in = None
        self._name_regex = name_regex
        self._note_on_bindings = defaultdict(list)

    def connect(self):
        inport_name = self._find(mido.get_input_names())
        outport_name = self._find(mido.get_output_names())

        if inport_name:
            self._inport = mido.open_input(inport_name)

        if outport_name:
            self._outport = mido.open_output(outport_name)

    # TODO: Enums
    def bind_note_on(self, note: int, callback: Awaitable[None]):
        self._note_on_bindings[note].append(callback)

    def bind_control_change(self, control: int, callback: Awaitable[None]):
        self._controls_bindings[control].append(callback)

    async def receive(self):
        while True:
            for msg in self._inport.iter_pending():
                logging.info(msg)
                await self._dispatch(msg)
            await asyncio.sleep(0.1)

    def _find(self, available: List[str]) -> Optional[str]:
        matching = [dev_name for dev_name in set(available) if self._name_regex.search(dev_name)]

        if len(matching) == 0:
            logging.warning(f'Could not find device matching {self._name_regex} (available devices: {available}')
            return None

        if len(matching) > 1:
            logging.warning(f'More than 1 device matched {self._name_regex} (available devices: {available}, '
                            f'picking first')

        return matching[0]

    async def _dispatch(self, msg: mido.Message):
        bindings = []
        if msg.type == MidiController.NOTE_ON:
            bindings = self._note_on_bindings[msg.note]
        elif msg.is_cc():
            bindings = self._controls_bindings[msg.control]

        logging.debug(f'Found {len(bindings)} bindings')
        for binding in bindings:
            await binding(msg)
