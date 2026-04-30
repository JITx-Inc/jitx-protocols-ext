"""SATA Protocol Example

This example demonstrates:
1. Host-to-device SATA connections
2. IC-to-IC SATA connections with null-modem style wiring
3. Blocking capacitors on TX paths
4. Signal integrity constraints with constrain_topology
"""

from jitx import Design, Net
from jitx.circuit import Circuit
from jitx.common import DiffPair

from examples.common.generic_fr4_board import ExampleBoard, ExampleSubstrate
from examples.common.example_components import BlockingCapacitor
from jitx_protocols_ext.protocols.sata import SATA
from .sata_components import SATASwitchCircuit


class DiffPairCoupler(Circuit):
    """Differential Pair Coupler using Blocking Capacitors

    This circuit creates a differential pair coupler using two blocking
    capacitors, one for each signal of the differential pair. It allows
    SI constraints to propagate through the capacitors via pin models.

    Args:
        capacitance: Capacitance value in Farads (default: 100nF)
    """

    A = DiffPair()
    B = DiffPair()

    def __init__(self, capacitance: float = 100.0e-9):
        # Create two blocking caps, one for P and one for N
        self.cap_p = BlockingCapacitor(capacitance)
        self.cap_n = BlockingCapacitor(capacitance)

        # Create topology chains through the capacitors
        self.topo_p1 = self.A.p >> self.cap_p.p1
        self.topo_p2 = self.cap_p.p2 >> self.B.p
        self.topo_n1 = self.A.n >> self.cap_n.p1
        self.topo_n2 = self.cap_n.p2 >> self.B.n


class SATAExampleCircuit(Circuit):
    """SATA Example Circuit

    This demonstrates two types of SATA connections:
    1. Host-to-device (passive connector) - straight TX->TX, RX->RX with
       blocking caps only on TX
    2. IC-to-IC - null-modem style with blocking caps on both TX and RX

    Uses SATA 3.0 constraints with 90Ω differential impedance.
    """

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        # Instantiate two SATA switch circuits
        self.dut1 = SATASwitchCircuit()
        self.dut2 = SATASwitchCircuit()

        # SATA 3.0 constraint setup
        generation = SATA.Generation.SATA3p0
        self.constraint = SATA.Constraint(generation)

        # Host-to-device connection (passive connector style)
        # Blocking caps only on TX path
        self.conn1 = self._setup_host_device_connection()

        # IC-to-IC connection (null-modem style)
        # With blocking caps on both TX and RX
        self.conn2 = self._setup_ic_to_ic_connection()

    def _setup_host_device_connection(self):
        """Setup host-to-device SATA connection

        SATA uses crossover topology (TX->RX):
        - src.TX -> blocking cap -> dst.RX (transmit to receive)
        - dst.TX -> src.RX (reverse path)
        """
        # Require SATA ports from each device
        src_ep = self.dut1.require(SATA())
        dst_ep = self.dut2.require(SATA())

        topos = []

        # Apply constraints using constrain_topology context manager
        with self.constraint.constrain_topology(src_ep, dst_ep) as (src, dst):
            # Create TX path with blocking caps (src TX -> dst RX)
            self.tx_coupler = DiffPairCoupler(100.0e-9)

            # TX path: src.TX -> coupler -> dst.RX (transmit to receive)
            topos.append([src.lane.TX >> self.tx_coupler.A])
            topos.append([self.tx_coupler.B >> dst.lane.RX])

            # RX path: dst.TX -> src.RX (reverse direction)
            topos.append([dst.lane.TX >> src.lane.RX])

        return topos

    def _setup_ic_to_ic_connection(self):
        """Setup IC-to-IC SATA connection

        For IC-to-IC connections (active to active):
        - TX->RX crossover with blocking caps on both sides
        - src.TX -> coupler -> dst.RX
        - dst.TX -> coupler -> src.RX
        """
        topos = []

        # Require SATA ports from each device
        src_ic = self.dut1.require(SATA())
        dst_ic = self.dut2.require(SATA())

        # Apply constraints
        with self.constraint.constrain_topology(src_ic, dst_ic) as (src, dst):
            # TX path: src.TX -> coupler -> dst.RX
            self.ic_tx_coupler = DiffPairCoupler(100.0e-9)
            topos.append([src.lane.TX >> self.ic_tx_coupler.A])
            topos.append([self.ic_tx_coupler.B >> dst.lane.RX])

            # RX path: dst.TX -> coupler -> src.RX
            self.ic_rx_coupler = DiffPairCoupler(100.0e-9)
            topos.append([dst.lane.TX >> self.ic_rx_coupler.A])
            topos.append([self.ic_rx_coupler.B >> src.lane.RX])

        return topos


class SATAExampleDesign(Design):
    """Complete SATA Example Design"""

    substrate = ExampleSubstrate()
    circuit = SATAExampleCircuit()
    board = ExampleBoard()
