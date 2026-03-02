"""DDR4 Protocol Example

This example demonstrates:
1. DDR4 memory-to-controller connection
2. FlyBy topology for command/address/control signals
3. Point-to-point topology for data signals
4. Signal integrity constraints with constrain_topology
"""

from jitx import Design, Net
from jitx.circuit import Circuit

from examples.common.example_board import ExampleBoard, ExampleSubstrate
from jitx_protocols_ext.protocols.memory.ddr4 import DDR4, DDR4Constraint, DDR4Rank, DDR4Width
from .ddr4_components import DDR4ControllerCircuit, DDR4MemoryCircuit


class DDR4ExampleCircuit(Circuit):
    """DDR4 Example Circuit

    This demonstrates DDR4 memory-to-controller connection with
    proper timing constraints for data and address/command/control signals.

    Uses DDR4 x16 configuration with:
    - 90Ω CK impedance
    - 100Ω DQS impedance
    - 50Ω DQ impedance
    - 45Ω ACC impedance
    """

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        # Instantiate memory and controller
        self.memory = DDR4MemoryCircuit()
        self.controller = DDR4ControllerCircuit()

        # DDR4 constraint setup
        self.constraint = DDR4Constraint(
            width=DDR4Width.x16,
            rank=DDR4Rank.SingleRank,
        )

        # Connect power
        self.power_nets = [
            self.GND + self.memory.pwr.Vn + self.controller.pwr.Vn,
            self.VDD + self.memory.pwr.Vp + self.controller.pwr.Vp,
        ]

        # Get DDR4 ports:
        # - Controller uses require() since it has Provide
        # - Memory uses direct io port since it has fixed connections
        ctrl_io = self.controller.require(DDR4(DDR4Width.x16, DDR4Rank.SingleRank))
        mem_io = self.memory.io

        # Connect DDR4 interface with constraints
        # DDR4 FlyBy topology:
        # - Data signals: Point-to-point (controller -> memory)
        # - ACC signals: FlyBy with tight timing to CK
        topos = []

        with self.constraint.constrain_topology(
            ctrl_io, mem_io
        ) as (src, dst):
            # Data channel connection (DQ, DQS, DM_n)
            for i in range(len(src.data.DQ)):
                topos.append([src.data.DQ[i] >> dst.data.DQ[i]])

            # DQS differential pairs
            for i in range(len(src.data.DQS)):
                topos.append([src.data.DQS[i] >> dst.data.DQS[i]])

            # DM_n signals
            for i in range(len(src.data.DM_n)):
                topos.append([src.data.DM_n[i] >> dst.data.DM_n[i]])

            # ACC channel connection (CK, address, command, control)
            for i in range(len(src.acc.CK)):
                topos.append([src.acc.CK[i] >> dst.acc.CK[i]])

            # Address bus
            for i in range(len(src.acc.A)):
                topos.append([src.acc.A[i] >> dst.acc.A[i]])

            # Bank address and group
            for i in range(len(src.acc.BA)):
                topos.append([src.acc.BA[i] >> dst.acc.BA[i]])
            for i in range(len(src.acc.BG)):
                topos.append([src.acc.BG[i] >> dst.acc.BG[i]])

            # Control signals
            for i in range(len(src.acc.CKE)):
                topos.append([src.acc.CKE[i] >> dst.acc.CKE[i]])
            for i in range(len(src.acc.CS_n)):
                topos.append([src.acc.CS_n[i] >> dst.acc.CS_n[i]])
            for i in range(len(src.acc.ODT)):
                topos.append([src.acc.ODT[i] >> dst.acc.ODT[i]])

            topos.append([src.acc.ACT_n >> dst.acc.ACT_n])
            topos.append([src.acc.RESET_n >> dst.acc.RESET_n])
            topos.append([src.acc.PAR >> dst.acc.PAR])
            topos.append([src.acc.ALERT_n >> dst.acc.ALERT_n])

        self.ddr4_topos = topos


class DDR4ExampleDesign(Design):
    """Complete DDR4 Example Design"""

    substrate = ExampleSubstrate()
    circuit = DDR4ExampleCircuit()
    board = ExampleBoard()
