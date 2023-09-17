from midi.program import Program
from midi.program_mapping_exception import ProgramMappingException


class ControllerMapping:
    def __init__(self):
        self._programs = []

    def map(self, program_id: int, program: Program):
        if program_id < 1:
            raise ProgramMappingException(f'Cannot map program {program_id} (programs start at 1)')

        self._programs[program_id - 1] = program

    def get(self, program_id: int) -> Program:
        if program_id < 1 or program_id >= len(self._programs) or self._programs[program_id - 1] is None:
            raise ProgramMappingException(f'Could not find program {program_id} (programs start at 1)')

        return self._programs[program_id - 1]
