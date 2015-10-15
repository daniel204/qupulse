from math import floor
import numpy
from typing import Dict, Any, Callable
from matlab.engine import MatlabEngine

from .Sequencer import SequencingHardwareInterface, InstructionBlock
from .Instructions import Waveform, EXECInstruction

__all__ = ["PulseControlInterface"]


class PulseControlInterface(SequencingHardwareInterface):

    @staticmethod
    def create_matlab_connected_interface(matlab_engine: MatlabEngine,
                                          sample_rate: float,
                                          time_scaling: float=0.001) -> "PulseControlInterface": #pragma: nocover
        register_pulse_callback = lambda x: matlab_engine.plsreg(matlab_engine.plsdefault(x))
        return PulseControlInterface(register_pulse_callback, sample_rate, time_scaling)

    def __init__(self, register_pulse_callback: Callable[[Dict[str, Any]], int], sample_rate: float, time_scaling: float=0.001) -> None:
        """Initialize PulseControlInterface.

        Arguments:
        pulse_registration_function -- A function which registers the pulse in pulse control and returns its id.
        sample_rate -- The rate in Hz at which waveforms are sampled.
        time_scaling -- A factor that scales the time domain defined in PulseTemplates. Defaults to 0.001, meaning
        that one unit of time in a PulseTemplate corresponds to one microsecond.
        """
        super().__init__()
        self.__sample_rate = sample_rate
        self.__time_scaling = time_scaling
        self.__register_pulse_callback = register_pulse_callback

    def __get_waveform_name(self, waveform: Waveform) -> str:
        return 'wf_{}'.format(hash(waveform))

    def register_waveform(self, waveform: Waveform) -> None:
        # Due to recent changes, Waveforms can always be recovered from the EXEC-Instructions.
        # Thus, register_waveform seems to have become obsolete (and with it the whole SequencingHardwareInterface).
        # Simply processing the InstructionBlock obtained from Sequencer seems to be sufficient.
        # However, before removing the Interface entirely, I would like to see whether or not this is still true
        # for real hardware interfaces.
        pass

    def create_waveform_struct(self, waveform: Waveform, name: str) -> Dict[str, Any]:
        """Construct a dictonary adhering to the waveform struct definition in pulse control.

        Arguments:
        waveform -- The Waveform object to convert.
        name -- Value for the name field in the resulting waveform dictionary."""
        sample_count = floor(waveform.duration * self.__time_scaling * self.__sample_rate) + 1
        sample_times = numpy.linspace(0, waveform.duration, sample_count)
        sampled_waveform = waveform.sample(sample_times)
        struct = dict(name=name,
                      data=dict(wf=sampled_waveform.tolist(),
                                marker=numpy.zeros_like(sampled_waveform).tolist(),
                                clk=self.__sample_rate))
        # TODO: how to deal with the second channel expected in waveform structs in pulse control?
        return struct

    def create_pulse_group(self, block: InstructionBlock, name: str) -> Dict[str, Any]:
        """Construct a dictonary adhering to the pulse group struct definition in pulse control.

        All waveforms in the given InstructionBlock are converted to waveform pulse structs and registered in
        pulse control with the pulse registration function held by the class. create_pulse_group detects
        multiple use of waveforms and sets up the pulse group dictionary accordingly.

        The function will raise an Exception if the given InstructionBlock does contain branching instructions,
        which are not supported by pulse control.

        Arguments:
        block -- The InstructionBlock to convert.
        name -- Value for the name field in the resulting pulse group dictionary.
        """
        if not all(map(lambda x: isinstance(x, EXECInstruction), block.instructions)):
            raise Exception("Hardware based branching is not supported by pulse-control.")

        waveforms = [instruction.waveform for instruction in block.instructions]
        if not waveforms:
            return ""

        pulse_group = dict(pulses=[],
                           nrep=[],
                           name=name,
                           chan=1,
                           ctrl='notrig')

        registered_waveforms = dict()

        for waveform in waveforms:
            if waveform not in registered_waveforms:
                name = self.__get_waveform_name(waveform)
                waveform_struct = self.create_waveform_struct(waveform, name)
                registered_waveforms[waveform] = self.__register_pulse_callback(waveform_struct)
            if pulse_group['pulses'] and pulse_group['pulses'][-1] == registered_waveforms[waveform]:
                pulse_group['nrep'][-1] += 1
            else:
                pulse_group['pulses'].append(registered_waveforms[waveform])
                pulse_group['nrep'].append(1)

        return pulse_group