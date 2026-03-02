# Memory Protocol Examples
#
# This package contains example components and designs for memory interfaces.

from .ddr4_components import DDR4ControllerCircuit, DDR4MemoryCircuit, DDR4MemoryComponent
from .ddr4_example import DDR4ExampleCircuit, DDR4ExampleDesign
from .gddr7_components import FBGA266, GDDR7ICCircuit, GDDR7MemoryCircuit, GDDR7MemoryComponent
from .gddr7_example import GDDR7ExampleCircuit, GDDR7ExampleDesign
from .lpddr4_components import K4FBE3D4HB_KHCL, LPDDR4ControllerCircuit, LPDDR4MemoryCircuit
from .lpddr4_example import LPDDR4ExampleCircuit, LPDDR4ExampleDesign
from .ddr5_components import DDR5ControllerCircuit, DDR5Memory, DDR5MemoryCircuit
from .ddr5_example import DDR5ExampleCircuit, DDR5ExampleDesign
from .lpddr5_components import LPDDR5ControllerCircuit, LPDDR5ControllerComponent
from .lpddr5_example import LPDDR5ExampleCircuit, LPDDR5ExampleDesign
from .MT62F4G32D8DV_026_AIT_B import MT62F4G32D8DV_026_AIT_B, LPDDR5MemoryCircuit

__all__ = [
    # DDR4
    "DDR4MemoryComponent",
    "DDR4MemoryCircuit",
    "DDR4ControllerCircuit",
    "DDR4ExampleCircuit",
    "DDR4ExampleDesign",
    # DDR5
    "DDR5Memory",
    "DDR5MemoryCircuit",
    "DDR5ControllerCircuit",
    "DDR5ExampleCircuit",
    "DDR5ExampleDesign",
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
