"""SFP Protocol Example

This example demonstrates:
1. SFP single-lane connections
2. QSFP multi-lane connections
3. IC-to-IC connections with null-modem style wiring
4. Blocking capacitors on TX paths
5. Signal integrity constraints with constrain_topology
"""

from jitx import Design, Net
from jitx.circuit import Circuit
from jitx.common import DiffPair

from ....common.example_board import ExampleBoard, ExampleSubstrate
from ....common.example_components import BlockingCapacitor
from ....protocols.sfp import QSFP, SFP, SFPConstraint, SFPLink
from .sfp_components import SFPSwitchCircuit


class DiffPairCoupler(Circuit):
    """Differential Pair Coupler using Blocking Capacitors

    This circuit creates a differential pair coupler using two blocking
    capacitors, one for each signal of the differential pair.

    Args:
        capacitance: Capacitance value in Farads (default: 100nF)
    """

    A = DiffPair()
    B = DiffPair()

    def __init__(self, capacitance: float = 100.0e-9):
        self.cap_p = BlockingCapacitor(capacitance)
        self.cap_n = BlockingCapacitor(capacitance)

        self.topo_p1 = self.A.p >> self.cap_p.p1
        self.topo_p2 = self.cap_p.p2 >> self.B.p
        self.topo_n1 = self.A.n >> self.cap_n.p1
        self.topo_n2 = self.cap_n.p2 >> self.B.n


class SFPExampleCircuit(Circuit):
    """SFP Example Circuit

    This demonstrates:
    1. SFP single-lane host-to-module connection with AC coupling
    2. QSFP 4-lane IC-to-IC connection with null-modem wiring

    Uses SFP+ constraints with 100Ω differential impedance.
    """

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        # Instantiate two SFP switch circuits
        self.dut1 = SFPSwitchCircuit()
        self.dut2 = SFPSwitchCircuit()

        # SFP+ constraint setup
        standard = SFPLink.SFP_PLUS
        self.constraint = SFPConstraint(standard.value)

        # QSFP+ constraint for multi-lane
        qsfp_standard = SFPLink.QSFP_PLUS
        self.qsfp_constraint = SFPConstraint(qsfp_standard.value)

        # Single-lane SFP connection (host-to-module style)
        self.conn1 = self._setup_sfp_connection()

        # 4-lane QSFP IC-to-IC connection
        self.conn2 = self._setup_qsfp_ic_to_ic_connection()

    def _setup_sfp_connection(self):
        """Setup single-lane SFP connection with AC coupling on TX

        SFP connections use crossover topology:
        - src.TX -> coupler -> dst.RX (transmit to receive)
        - dst.TX -> src.RX (reverse path)
        """
        # Require SFP ports from each device
        src_ep = self.dut1.require(SFP())
        dst_ep = self.dut2.require(SFP())

        topos = []

        # Apply constraints
        with self.constraint.constrain_topology(src_ep, dst_ep) as (src, dst):
            # Create TX path with blocking caps (src TX -> dst RX)
            self.tx_coupler = DiffPairCoupler(100.0e-9)

            # TX path: src.TX -> coupler -> dst.RX (transmit to receive)
            topos.append([src.lanes[0].TX >> self.tx_coupler.A])
            topos.append([self.tx_coupler.B >> dst.lanes[0].RX])

            # RX path: dst.TX -> src.RX (reverse direction)
            topos.append([dst.lanes[0].TX >> src.lanes[0].RX])

        return topos

    def _setup_qsfp_ic_to_ic_connection(self):
        """Setup 4-lane QSFP IC-to-IC connection

        QSFP connections use crossover topology (TX->RX):
        - src.TX -> coupler -> dst.RX
        - dst.TX -> coupler -> src.RX
        """
        topos = []

        # Require QSFP ports from each device
        src_ic = self.dut1.require(QSFP())
        dst_ic = self.dut2.require(QSFP())

        # Apply constraints
        with self.qsfp_constraint.constrain_topology(src_ic, dst_ic) as (src, dst):
            # Create TX/RX paths with blocking caps for all 4 lanes
            self.ic_tx_couplers = []
            self.ic_rx_couplers = []

            for i in range(4):
                # TX path: src.TX -> coupler -> dst.RX
                tx_coupler = DiffPairCoupler(100.0e-9)
                self.ic_tx_couplers.append(tx_coupler)
                topos.append([src.lanes[i].TX >> tx_coupler.A])
                topos.append([tx_coupler.B >> dst.lanes[i].RX])

                # RX path: dst.TX -> coupler -> src.RX
                rx_coupler = DiffPairCoupler(100.0e-9)
                self.ic_rx_couplers.append(rx_coupler)
                topos.append([dst.lanes[i].TX >> rx_coupler.A])
                topos.append([rx_coupler.B >> src.lanes[i].RX])

        return topos


class SFPExampleDesign(Design):
    """Complete SFP Example Design"""

    substrate = ExampleSubstrate()
    circuit = SFPExampleCircuit()
    board = ExampleBoard()
