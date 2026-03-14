"""LPDDR4 Protocol Example

Translation of lpddr4_demo Stanza project to Python.

This example demonstrates:
1. LPDDR4 memory-to-controller connection (x32 = 2 x16 channels)
2. Memory component with Provide() for pin optionality
3. Controller component with Provide() for pin optionality
4. Signal integrity constraints from LPDDR4Constraint
"""

from jitx import Design, Net
from jitx.circuit import Circuit

from examples.common.example_board import ExampleBoard, ExampleSubstrate
from jitx_protocols_ext.protocols.memory.lpddr4 import (
    LPDDR4,
    LPDDR4Constraint,
    LPDDR4Rank,
    LPDDR4Width,
)

from .lpddr4_components import LPDDR4ControllerCircuit, LPDDR4MemoryCircuit


class LPDDR4ExampleCircuit(Circuit):
    """LPDDR4 Example Circuit

    Translation of lpddr4_demo main.stanza.

    This demonstrates LPDDR4 x32 memory-to-controller connection with
    proper timing constraints:
    - CK to CKE/CS skew: ±8ps
    - CK to CA skew: ±8ps
    - CK to DQS skew: -500ps to +2500ps
    - DQS to DQ/DMI skew: ±5ps
    """

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        # Instantiate memory and controller
        self.memory = LPDDR4MemoryCircuit()
        self.controller = LPDDR4ControllerCircuit()

        # LPDDR4 constraint setup
        self.constraint = LPDDR4Constraint(
            width=LPDDR4Width.x32,
            rank=LPDDR4Rank.Rank2,
        )

        # Power nets — memory has 3 separate rails, all sharing VSS
        self.GND += self.memory.pwr_vdd1.Vn + self.controller.pwr.Vn
        self.VDD += self.controller.pwr.Vp

        self.VDD1 = Net(name="VDD1")
        self.VDD1 += self.memory.pwr_vdd1.Vp

        self.VDD2 = Net(name="VDD2")
        self.VDD2 += self.memory.pwr_vdd2.Vp

        self.VDDQ = Net(name="VDDQ")
        self.VDDQ += self.memory.pwr_vddq.Vp

        # Get LPDDR4 ports via require() — both use Provide
        ctrl_io = self.controller.require(LPDDR4(LPDDR4Width.x32, LPDDR4Rank.Rank2))
        mem_io = self.memory.require(LPDDR4(LPDDR4Width.x32, LPDDR4Rank.Rank2))

        # Connect LPDDR4 interface with constraints
        # All connections must be directly in __init__ (not in helper method)
        topos = []

        with self.constraint.constrain_topology(ctrl_io, mem_io) as (src, dst):
            # Connect all channels (x32 = 2 x16 channels)
            for ch_idx in range(2):
                src_ch = src.ch[ch_idx]
                dst_ch = dst.ch[ch_idx]

                # CK connection (differential pair)
                topos.append([src_ch.ck >> dst_ch.ck])

                # CKE connections (per rank)
                for i in range(len(src_ch.cke)):
                    topos.append([src_ch.cke[i] >> dst_ch.cke[i]])

                # CS connections (per rank)
                for i in range(len(src_ch.cs)):
                    topos.append([src_ch.cs[i] >> dst_ch.cs[i]])

                # CA connections (6 bits per channel)
                for i in range(len(src_ch.ca)):
                    topos.append([src_ch.ca[i] >> dst_ch.ca[i]])

                # Data lane connections (2 lanes per channel)
                for lane_idx in range(2):
                    src_lane = src_ch.d[lane_idx]
                    dst_lane = dst_ch.d[lane_idx]

                    # DQS (differential pair)
                    topos.append([src_lane.dqs >> dst_lane.dqs])

                    # DQ (8 bits per lane)
                    for i in range(len(src_lane.dq)):
                        topos.append([src_lane.dq[i] >> dst_lane.dq[i]])

                    # DMI
                    topos.append([src_lane.dmi >> dst_lane.dmi])

        self.lpddr4_topos = topos


class LPDDR4ExampleDesign(Design):
    """Complete LPDDR4 Example Design"""

    substrate = ExampleSubstrate()
    circuit = LPDDR4ExampleCircuit()
    board = ExampleBoard()
