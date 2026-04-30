"""JESD204 Protocol Example

This example demonstrates:
1. ADC-to-FPGA JESD204B connection with 4 serial lanes
2. Direct DC-coupled data lane routing (no AC coupling needed)
3. SYNC~ signal routing from FPGA back to ADC
4. SYSREF and DEVCLK clock routing
5. Signal integrity constraints with constrain_topology
"""

from jitx import Design, Net
from jitx.circuit import Circuit

from examples.common.generic_fr4_board import ExampleBoard, ExampleSubstrate
from jitx_protocols_ext.protocols.jesd204 import JESD204, JESD204Constraint, JESD204LaneCount, JESD204Version
from .jesd204_components import JESD204ADCCircuit, JESD204FPGACircuit


class JESD204ExampleCircuit(Circuit):
    """JESD204 Example Circuit

    Demonstrates a 4-lane JESD204B connection between a quad ADC and
    an FPGA. Uses Subclass 1 (with SYSREF for deterministic latency).

    JESD204 data lanes are DC-coupled CML, so no blocking capacitors
    are needed on the data path (unlike PCIe or SATA).

    Topology:
    - ADC SERDOUT[0:3] → FPGA SERDIN[0:3] (4 data lanes)
    - FPGA SYNC~ → ADC SYNC~ (sync signal, opposite direction)
    - SYSREF → ADC, FPGA (system reference clock)
    - DEVCLK → ADC, FPGA (device clock)
    """

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        self.adc = JESD204ADCCircuit()
        self.fpga = JESD204FPGACircuit()

        # JESD204B constraint setup (Subclass 1 with SYSREF)
        version = JESD204Version.JESD204B
        self.constraint = JESD204Constraint(version.value)

        self.conn = self._setup_adc_to_fpga_connection()

    def _setup_adc_to_fpga_connection(self):
        """Setup ADC-to-FPGA JESD204B connection

        JESD204 data lanes are unidirectional (ADC TX → FPGA RX).
        Each lane is a single DiffPair, routed directly without
        AC coupling capacitors.

        SYNC~ flows in the opposite direction (FPGA → ADC).
        """
        # Require 4-lane JESD204 ports from each device
        src_ep = self.adc.require(JESD204(JESD204LaneCount.x4))
        dst_ep = self.fpga.require(JESD204(JESD204LaneCount.x4))

        topos = []

        with self.constraint.constrain_topology(src_ep, dst_ep) as (src, dst):
            # Data lanes: direct routing (DC-coupled, no blocking caps)
            for i in range(len(src.lane)):
                topos.append([src.lane[i] >> dst.lane[i]])

            # SYNC~: FPGA (receiver) drives SYNC~ back to ADC (transmitter)
            if src.SYNC is not None and dst.SYNC is not None:
                topos.append([dst.SYNC >> src.SYNC])

            # SYSREF: straight through
            if src.SYSREF is not None and dst.SYSREF is not None:
                topos.append([src.SYSREF >> dst.SYSREF])

            # DEVCLK: straight through
            if src.DEVCLK is not None and dst.DEVCLK is not None:
                topos.append([src.DEVCLK >> dst.DEVCLK])

        return topos


class JESD204ExampleDesign(Design):
    """Complete JESD204 Example Design"""

    substrate = ExampleSubstrate()
    circuit = JESD204ExampleCircuit()
    board = ExampleBoard()
