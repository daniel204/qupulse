"""STANDARD LIBRARY IMPORTS"""
from abc import ABCMeta, abstractmethod
from typing import Dict, List, Tuple, Set
import logging

"""RELATED THIRD PARTY IMPORTS"""

"""LOCAL IMPORTS"""
from Parameter import ParameterDeclaration, Parameter
from HardwareUploadInterface import Waveform

logger = logging.getLogger(__name__)

class PulseTemplate(metaclass = ABCMeta):
    """!@brief A PulseTemplate represents the parametrized general structure of a pulse.
    
    A PulseTemplate described a pulse in an abstract way: It defines the structure of a pulse
    but might leave some timings or voltage levels undefined, thus declaring parameters.
    This allows to reuse a PulseTemplate for several pulses which have the same overall structure
    and differ only in concrete values for the parameters.
    Obtaining an actual pulse which can be executed by specifying values for these parameters is
    called instantiation of the PulseTemplate.
    """
    
    def __init__(self):
        super().__init__()
        
    @abstractmethod
    def __len__(self) -> int:
        """Defines the behaviour of len(PulseTemplate), which is the sum of all subpulses. 
        __len__ already provides a type check to assure that only numerical values are returned
        """
        # TODO: decide whether or not measuring the length of a PulseTemplate actually makes sense, since it may depend on parameters (maybe move to Pulse)
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass
    
    @abstractmethod
    def get_parameter_names(self) -> Set[str]:
        """!@brief Return the set of names of declared parameters."""
        pass
        
    @abstractmethod
    def get_parameter_declarations(self) -> Dict[str, ParameterDeclaration]:
        """!@brief Return a copy of the dictionary containing the parameter declarations of this PulseTemplate."""
        pass

    @abstractmethod
    def get_measurement_windows(self) -> List[Tuple[float, float]]:
        """!@brief Return all measurment windows defined in this PulseTemplate."""
        # TODO: decide whether or not defining exact measurment windows on templates makes sense (maybe move to Pulse)
        pass

    @abstractmethod
    def is_interruptable(self) -> bool:
        """!@brief Return true, if this PulseTemplate contains points at which it can halt if interrupted."""
        pass

    @abstractmethod
    def upload_waveform(self, uploadInterface: HardwareUploadInterface, parameters: Dict[str, Parameter]) -> Waveform:
        """!@brief Compile a waveform of the pulse represented by this PulseTemplate and the given parameters using the given HardwareUploadInterface object."""
        pass


class ParameterNotInPulseTemplateException(Exception):
    """!@brief Indicates that a provided parameter was not declared in a PulseTemplate."""
    
    def __init__(self, name: str, pulse_template: PulseTemplate):
        super().__init__()
        self.name = name
        self.pulse_template = pulse_template

    def __str__(self):
        return "Parameter {1} not found".format(self.name)