"""DDR4 Protocol Example

Demonstrates DDR4 x16 memory-to-controller connection with full signal
integrity constraints applied via DDR4Constraint.constrain_topology().
"""

from jitx import Design, Net
from jitx.circuit import Circuit

from examples.common.example_board import ExampleBoard, ExampleSubstrate
from jitx_protocols_ext.protocols.memory.ddr4 import (
    DDR4,
    DDR4Constraint,
    DDR4Rank,
    DDR4Width,
)

from .ddr4_components import DDR4ControllerCircuit, DDR4MemoryCircuit


class DDR4ExampleCircuit(Circuit):
    """DDR4 x16 Example Circuit

    Point-to-point DDR4 x16 memory-to-controller with SI constraints:
    - 90 Ohm CK, 100 Ohm DQS, 50 Ohm DQ, 45 Ohm ACC impedances
    - +/-1.0ps DQS/CK intra-pair skew
    - +/-3.5ps DQ-to-DQS, +/-20ps ACC-to-CK timing
    - 5 dB max insertion loss
    """

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        self.memory = DDR4MemoryCircuit()
        self.controller = DDR4ControllerCircuit()

        self.power_nets = [
            self.GND + self.memory.pwr.Vn + self.controller.pwr.Vn,
            self.VDD + self.memory.pwr.Vp + self.controller.pwr.Vp,
        ]

        self.constraint = DDR4Constraint(width=DDR4Width.x16, rank=DDR4Rank.SingleRank)
        ctrl_io = self.controller.require(DDR4(DDR4Width.x16, DDR4Rank.SingleRank))
        mem_io = self.memory.io

        topos = []
        with self.constraint.constrain_topology(ctrl_io, mem_io) as (src, dst):
            for i in range(len(src.data.DQ)):
                topos.append([src.data.DQ[i] >> dst.data.DQ[i]])
            for i in range(len(src.data.DQS)):
                topos.append([src.data.DQS[i] >> dst.data.DQS[i]])
            for i in range(len(src.data.DM_n)):
                topos.append([src.data.DM_n[i] >> dst.data.DM_n[i]])
            for i in range(len(src.acc.CK)):
                topos.append([src.acc.CK[i] >> dst.acc.CK[i]])
            for i in range(len(src.acc.A)):
                topos.append([src.acc.A[i] >> dst.acc.A[i]])
            for i in range(len(src.acc.BA)):
                topos.append([src.acc.BA[i] >> dst.acc.BA[i]])
            for i in range(len(src.acc.BG)):
                topos.append([src.acc.BG[i] >> dst.acc.BG[i]])
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
