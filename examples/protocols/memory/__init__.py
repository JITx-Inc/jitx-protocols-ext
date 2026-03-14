# Memory Protocol Examples
#
# This package contains example components and designs for memory interfaces.

from .ddr4_components import DDR4ControllerCircuit, DDR4MemoryCircuit, DDR4MemoryComponent
from .ddr4_example import DDR4ExampleCircuit, DDR4ExampleDesign
from .ddr5_components import (
    DDR5_x4x8_78ball,
    DDR5_x4x8_82ball,
    DDR5_x16_102ball,
    DDR5_x16_106ball,
    DDR5ControllerCircuit,
    DDR5ControllerCircuit_x16,
    DDR5Memory,
    DDR5MemoryCircuit,
    DDR5MemoryCircuit_x8,
    DDR5MemoryCircuit_x16,
)
from .ddr5_example import DDR5ExampleCircuit, DDR5ExampleDesign
from .ddr5_x16_example import DDR5x16ExampleCircuit, DDR5x16ExampleDesign
from .gddr7_components import FBGA266, GDDR7ICCircuit, GDDR7MemoryCircuit, GDDR7MemoryComponent
from .gddr7_example import GDDR7ExampleCircuit, GDDR7ExampleDesign
from .lpddr4_components import K4FBE3D4HB_KHCL, LPDDR4ControllerCircuit, LPDDR4MemoryCircuit
from .lpddr4_example import LPDDR4ExampleCircuit, LPDDR4ExampleDesign
from .lpddr5_components import LPDDR5ControllerCircuit, LPDDR5ControllerComponent
from .lpddr5_example import LPDDR5ExampleCircuit, LPDDR5ExampleDesign
from .MT40A1G16TB_062E_F import DDR4SingleMemoryCircuit
from .MT62F4G32D8DV_026_AIT_B import MT62F4G32D8DV_026_AIT_B, LPDDR5MemoryCircuit

__all__ = [
    # GDDR7
    "FBGA266",
    # LPDDR4
    "K4FBE3D4HB_KHCL",
    # LPDDR5
    "MT62F4G32D8DV_026_AIT_B",
    "DDR4ControllerCircuit",
    "DDR4ExampleCircuit",
    "DDR4ExampleDesign",
    "DDR4MemoryCircuit",
    # DDR4
    "DDR4MemoryComponent",
    "DDR4SingleMemoryCircuit",
    "DDR5ControllerCircuit",
    "DDR5ControllerCircuit_x16",
    "DDR5ExampleCircuit",
    "DDR5ExampleDesign",
    "DDR5Memory",
    "DDR5MemoryCircuit",
    "DDR5MemoryCircuit_x8",
    "DDR5MemoryCircuit_x16",
    # DDR5
    "DDR5_x4x8_78ball",
    "DDR5_x4x8_82ball",
    "DDR5_x16_102ball",
    "DDR5_x16_106ball",
    "DDR5x16ExampleCircuit",
    "DDR5x16ExampleDesign",
    "GDDR7ExampleCircuit",
    "GDDR7ExampleDesign",
    "GDDR7ICCircuit",
    "GDDR7MemoryCircuit",
    "GDDR7MemoryComponent",
    "LPDDR4ControllerCircuit",
    "LPDDR4ExampleCircuit",
    "LPDDR4ExampleDesign",
    "LPDDR4MemoryCircuit",
    "LPDDR5ControllerCircuit",
    "LPDDR5ControllerComponent",
    "LPDDR5ExampleCircuit",
    "LPDDR5ExampleDesign",
    "LPDDR5MemoryCircuit",
]
