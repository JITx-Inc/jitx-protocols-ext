# Memory Protocol Examples
#
# This package contains example components and designs for memory interfaces.

from .ddr4_components import DDR4MemoryComponent, DDR4MemoryCircuit, DDR4ControllerCircuit
from .ddr4_example import DDR4ExampleCircuit, DDR4ExampleDesign
from .lpddr4_components import K4FBE3D4HB_KHCL, LPDDR4MemoryCircuit, LPDDR4ControllerCircuit
from .lpddr4_example import LPDDR4ExampleCircuit, LPDDR4ExampleDesign
from .MT62F4G32D8DV_026_AIT_B import MT62F4G32D8DV_026_AIT_B, LPDDR5MemoryCircuit
from .lpddr5_components import LPDDR5ControllerComponent, LPDDR5ControllerCircuit
from .lpddr5_example import LPDDR5ExampleCircuit, LPDDR5ExampleDesign
from .gddr7_components import GDDR7MemoryComponent, GDDR7MemoryCircuit, GDDR7ICCircuit, FBGA266
from .gddr7_example import GDDR7ExampleCircuit, GDDR7ExampleDesign

__all__ = [
    # DDR4
    "DDR4MemoryComponent",
    "DDR4MemoryCircuit",
    "DDR4ControllerCircuit",
    "DDR4ExampleCircuit",
    "DDR4ExampleDesign",
    # LPDDR4
    "K4FBE3D4HB_KHCL",
    "LPDDR4MemoryCircuit",
    "LPDDR4ControllerCircuit",
    "LPDDR4ExampleCircuit",
    "LPDDR4ExampleDesign",
    # LPDDR5
    "MT62F4G32D8DV_026_AIT_B",
    "LPDDR5MemoryCircuit",
    "LPDDR5ControllerComponent",
    "LPDDR5ControllerCircuit",
    "LPDDR5ExampleCircuit",
    "LPDDR5ExampleDesign",
    # GDDR7
    "FBGA266",
    "GDDR7MemoryComponent",
    "GDDR7MemoryCircuit",
    "GDDR7ICCircuit",
    "GDDR7ExampleCircuit",
    "GDDR7ExampleDesign",
]
