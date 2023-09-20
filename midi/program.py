from typing import List

from midi.program_mapping_exception import ProgramMappingException


class Program:
    def __init__(self, pads: List[int], knobs: List[int]):
        self._pads = pads
        self._knobs = knobs

    def get_pad(self, pad: int):
        """
        :param pad: (one-based)
        :return:
        """
        if pad > len(self._pads) or pad < 1:
            raise ProgramMappingException(f'Pad {pad} is not mapped')

        return self._pads[pad - 1]

    def get_knob(self, knob: int):
        """
        :param knob: (one-based)
        :return:
        """
        if knob > len(self._knobs) or knob < 1:
            raise ProgramMappingException(f'Knob {knob} is not mapped')

        return self._knobs[knob - 1]
