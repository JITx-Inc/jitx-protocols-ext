"""GDDR7 Protocol Example

Translation of jsl/examples/protocols/memory/gddr7 to Python.

This example demonstrates:
1. GDDR7 memory component with FBGA266 package
2. GDDR7 GPU/IC component
3. Connecting GDDR7 devices with proper constraints
4. 4-channel configuration with RCK/WCK clocking
"""

from jitx import Design, Net
from jitx.circuit import Circuit

from ....common.example_board import ExampleBoard, ExampleSubstrate
from ....protocols.memory.gddr7 import GDDR7, GDDR7Constraint
from .gddr7_components import GDDR7ICCircuit, GDDR7MemoryCircuit


class GDDR7ExampleCircuit(Circuit):
    """GDDR7 Example Circuit

    This demonstrates GDDR7 GPU-to-memory connection with
    proper timing constraints for all 4 data channels.

    GDDR7 timing constraints:
    - RCK intra-pair skew: ±10fs
    - WCK intra-pair skew: ±10fs
    - RCK to WCK skew: ±20ps
    - WCK to CA skew: ±20ps
    - RCK/WCK to DQ/DQE skew: ±20ps
    - DQ to DQE skew: ±5ps
    - CA to CA skew: ±5ps
    """

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        # Instantiate memory and GPU
        self.dut1 = GDDR7MemoryCircuit()
        self.dut2 = GDDR7ICCircuit()

        # GDDR7 constraint setup
        self.constraint = GDDR7Constraint()

        # Power nets
        self.power_nets = [
            self.GND + self.dut1.pwr.Vn + self.dut2.pwr.Vn,
            self.VDD + self.dut1.pwr.Vp + self.dut2.pwr.Vp,
        ]

        # Connect GDDR7 interface with constraints
        self.gddr7_conn = self._setup_gddr7_connection()

    def _setup_gddr7_connection(self):
        """Setup GDDR7 connection with constraints"""
        topos = []

        # Get GDDR7 port from IC using require (equivalent to Stanza's require)
        ic_io = self.dut2.require(GDDR7())

        # Apply constraints
        with self.constraint.constrain_topology(
            ic_io, self.dut1.io  # GPU -> Memory
        ) as (src, dst):
            # Connect each of the 4 data channels
            for ch_idx in range(4):
                src_ch = src.data[ch_idx]
                dst_ch = dst.data[ch_idx]

                # RCK
                topos.append([src_ch.RCK >> dst_ch.RCK])

                # WCK
                topos.append([src_ch.WCK >> dst_ch.WCK])

                # DQ (10 per channel)
                for dq_idx in range(10):
                    topos.append([src_ch.DQ[dq_idx] >> dst_ch.DQ[dq_idx]])

                # CA (5 per channel)
                for ca_idx in range(5):
                    topos.append([src_ch.CA[ca_idx] >> dst_ch.CA[ca_idx]])

                # DQE
                topos.append([src_ch.DQE >> dst_ch.DQE])

                # ERR
                topos.append([src_ch.ERR >> dst_ch.ERR])

            # Control signals
            topos.append([src.control.RESET_n >> dst.control.RESET_n])
            topos.append([src.control.ZQ_AB >> dst.control.ZQ_AB])
            topos.append([src.control.ZQ_CD >> dst.control.ZQ_CD])

        return topos


class GDDR7ExampleDesign(Design):
    """Complete GDDR7 Example Design"""

    substrate = ExampleSubstrate()
    circuit = GDDR7ExampleCircuit()
    board = ExampleBoard()
