"""DDR5 Protocol Example

This example demonstrates:
1. DDR5 memory-to-controller connection using the Micron MT60B2G8HB-48B
2. Point-to-point topology for data and CA signals
3. Signal integrity constraints with constrain_topology
4. DDR5's unified 14-bit CA bus (vs DDR4's separate A/BA/BG)
"""

from jitx import Design, Net
from jitx.circuit import Circuit

from examples.common.example_board import ExampleBoard, ExampleSubstrate
from jitx_protocols_ext.protocols.memory.ddr5 import DDR5, DDR5Constraint, DDR5Rank, DDR5Width

from .ddr5_components import DDR5ControllerCircuit, DDR5MemoryCircuit


class DDR5ExampleCircuit(Circuit):
    """DDR5 Example Circuit

    DDR5 x16 memory-to-controller connection with signal integrity constraints.

    Uses DDR5 x16 configuration with:
    - 80Ω CK impedance (differential)
    - 80Ω DQS impedance (differential)
    - 40Ω DQ impedance (single-ended)
    - 40Ω CA impedance (single-ended, PODL)
    """

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        self.memory = DDR5MemoryCircuit()
        self.controller = DDR5ControllerCircuit()

        self.constraint = DDR5Constraint(
            width=DDR5Width.x16,
            rank=DDR5Rank.SingleRank,
        )

        # Connect power
        self.power_nets = [
            self.GND + self.memory.pwr.Vn + self.controller.pwr.Vn,
            self.VDD + self.memory.pwr.Vp + self.controller.pwr.Vp,
        ]

        # Get DDR5 ports:
        # - Controller uses require() since it has Provide
        # - Memory uses direct io port since it has fixed connections
        ctrl_io = self.controller.require(DDR5(DDR5Width.x16, DDR5Rank.SingleRank))
        mem_io = self.memory.io

        # Connect DDR5 interface with constraints
        topos = []

        with self.constraint.constrain_topology(
            ctrl_io, mem_io
        ) as (src, dst):
            # Data channel connection (DQ, DQS, DMI)
            for i in range(len(src.data.DQ)):
                topos.append([src.data.DQ[i] >> dst.data.DQ[i]])

            # DQS differential pairs
            for i in range(len(src.data.DQS)):
                topos.append([src.data.DQS[i] >> dst.data.DQS[i]])

            # DMI signals
            for i in range(len(src.data.DMI)):
                topos.append([src.data.DMI[i] >> dst.data.DMI[i]])

            # CA channel connection
            # CK differential pair
            topos.append([src.ca.CK >> dst.ca.CK])

            # CA bus (14 bits)
            for i in range(len(src.ca.CA)):
                topos.append([src.ca.CA[i] >> dst.ca.CA[i]])

            # Control signals
            for i in range(len(src.ca.CKE)):
                topos.append([src.ca.CKE[i] >> dst.ca.CKE[i]])
            for i in range(len(src.ca.CS_n)):
                topos.append([src.ca.CS_n[i] >> dst.ca.CS_n[i]])
            for i in range(len(src.ca.ODT)):
                topos.append([src.ca.ODT[i] >> dst.ca.ODT[i]])

            topos.append([src.ca.RESET_n >> dst.ca.RESET_n])
            topos.append([src.ca.ALERT_n >> dst.ca.ALERT_n])

        self.ddr5_topos = topos


class DDR5ExampleDesign(Design):
    """Complete DDR5 Example Design"""

    substrate = ExampleSubstrate()
    circuit = DDR5ExampleCircuit()
    board = ExampleBoard()
