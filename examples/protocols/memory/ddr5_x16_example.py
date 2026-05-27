"""DDR5 x16 Protocol Example

Demonstrates DDR5 x16 memory-to-controller connection using the 102-ball
SDRAM component with dual byte-lane topology and full SI constraints applied
via DDR5Constraint.constrain_topology().
"""

from jitx import Design, Net
from jitx.circuit import Circuit

from examples.common.example_board import ExampleBoard, ExampleSubstrate
from jitx_protocols_ext.protocols.memory.ddr5 import (
    DDR5,
    DDR5Constraint,
    DDR5Rank,
    DDR5Width,
)

from .ddr5_components import DDR5ControllerCircuit_x16, DDR5MemoryCircuit_x16


class DDR5x16ExampleCircuit(Circuit):
    """DDR5 x16 Example Circuit

    Point-to-point DDR5 x16 memory-to-controller with SI constraints:
    - 80 Ohm CK/DQS, 40 Ohm DQ/CA impedances
    - 2 byte lanes (upper + lower), each with DQS and DMI
    - +/-0.5ps DQS/CK intra-pair skew
    - +/-2.5ps DQ-to-DQS, +/-15ps CA-to-CK timing
    - 5 dB max insertion loss
    """

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        self.memory = DDR5MemoryCircuit_x16()
        self.controller = DDR5ControllerCircuit_x16()

        # Power nets — memory has separate VDD, VDDQ, VPP rails
        self.GND += self.memory.pwr_vdd.Vn + self.controller.pwr.Vn
        self.VDD += self.controller.pwr.Vp

        self.MEM_VDD = Net(name="MEM_VDD")
        self.MEM_VDD += self.memory.pwr_vdd.Vp

        self.MEM_VDDQ = Net(name="MEM_VDDQ")
        self.MEM_VDDQ += self.memory.pwr_vddq.Vp

        self.MEM_VPP = Net(name="MEM_VPP")
        self.MEM_VPP += self.memory.pwr_vpp.Vp

        self.constraint = DDR5Constraint(width=DDR5Width.x16, rank=DDR5Rank.SingleRank)
        ctrl_io = self.controller.require(DDR5(DDR5Width.x16, DDR5Rank.SingleRank))
        mem_io = self.memory.require(DDR5(DDR5Width.x16, DDR5Rank.SingleRank))

        topos = []
        with self.constraint.constrain_topology(ctrl_io, mem_io) as (src, dst):
            for i in range(len(src.data.DQ)):
                topos.append([src.data.DQ[i] >> dst.data.DQ[i]])
            for i in range(len(src.data.DQS)):
                topos.append([src.data.DQS[i] >> dst.data.DQS[i]])
            for i in range(len(src.data.DMI)):
                topos.append([src.data.DMI[i] >> dst.data.DMI[i]])
            topos.append([src.ca.CK >> dst.ca.CK])
            for i in range(len(src.ca.CA)):
                topos.append([src.ca.CA[i] >> dst.ca.CA[i]])
            for i in range(len(src.ca.CS_n)):
                topos.append([src.ca.CS_n[i] >> dst.ca.CS_n[i]])
            topos.append([src.ca.RESET_n >> dst.ca.RESET_n])
            topos.append([src.ca.ALERT_n >> dst.ca.ALERT_n])
        self.ddr5_topos = topos


class DDR5x16ExampleDesign(Design):
    """Complete DDR5 x16 Example Design"""

    substrate = ExampleSubstrate()
    circuit = DDR5x16ExampleCircuit()
    board = ExampleBoard()
