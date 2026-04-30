"""PCIe Protocol Example

Translation of jsl/examples/protocols/pcie/pcie-main.stanza

This example demonstrates:
1. Card edge PCIe connections (passive connector setup)
2. IC-to-IC PCIe connections with null-modem style wiring
3. Blocking capacitors on TX paths
4. Signal integrity constraints with constrain_topology
"""

from jitx import Design, Net
from jitx.circuit import Circuit
from jitx.common import DiffPair
from jitx.si import SignalConstraint

from examples.common.generic_fr4_board import ExampleBoard, ExampleSubstrate
from examples.common.example_components import BlockingCapacitor
from jitx_protocols_ext.protocols.pcie import (
    PCIe,
    PCIeConstraint,
    PCIeVersion,
    PCIeWidth,
    connect_pcie_null_modem,
)
from .pcie_components import PCIeSwitchCircuit


class DiffPairCoupler(Circuit):
    """Differential Pair Coupler using Blocking Capacitors

    Translation of dp-coupler from jsl/si/couplers.stanza.

    This circuit creates a differential pair coupler using two blocking
    capacitors, one for each signal of the differential pair. It allows
    SI constraints to propagate through the capacitors via pin models.

    Args:
        capacitance: Capacitance value in Farads (default: 220nF)
    """

    A = DiffPair()
    B = DiffPair()

    def __init__(self, capacitance: float = 220.0e-9):
        # Create two blocking caps, one for P and one for N
        self.cap_p = BlockingCapacitor(capacitance)
        self.cap_n = BlockingCapacitor(capacitance)

        # Create topology chains through the capacitors
        # The >> operator creates both nets and topology
        self.topo_p1 = self.A.p >> self.cap_p.p1
        self.topo_p2 = self.cap_p.p2 >> self.B.p
        self.topo_n1 = self.A.n >> self.cap_n.p1
        self.topo_n2 = self.cap_n.p2 >> self.B.n


class PCIeExampleCircuit(Circuit):
    """PCIe Example Circuit

    Translation of pcie-example from pcie-main.stanza.

    This demonstrates two types of PCIe connections:
    1. Card edge (passive connector) - straight TX->TX, RX->RX with
       blocking caps only on TX
    2. IC-to-IC - null-modem style with blocking caps on both TX and RX

    Uses PCIe V4 constraints with 85Ω differential impedance.
    """

    GND = Net(name="GND")
    VDD = Net(name="VDD")

    def __init__(self):
        # Instantiate two PCIe switch circuits (like dut1 and dut2)
        self.dut1 = PCIeSwitchCircuit()
        self.dut2 = PCIeSwitchCircuit()

        # PCIe V4 constraint setup
        version = PCIeVersion.V4
        self.constraint = PCIeConstraint(version.value)
        self.constraint_xover = PCIeConstraint(version.value, xover=True)

        # Card edge connection (passive connector style)
        # Straight through: tx -> tx, rx -> rx
        # Blocking caps only on TX path
        self.conn1 = self._setup_card_edge_connection(self.constraint)

        # IC-to-IC connection (null-modem style)
        # With blocking caps on both TX and RX
        self.conn2 = self._setup_ic_to_ic_connection(self.constraint_xover)

    def _setup_card_edge_connection(self, constraint: SignalConstraint[PCIe]):
        """Setup card edge PCIe connection

        Translation of the first constrain-topology block in pcie-main.stanza.

        For card edge (passive connector) connections:
        - TX -> blocking cap -> TX
        - RX -> RX (no blocking cap)
        - Control signals connected directly
        """
        # Require x2 PCIe ports from each device
        src_ep = self.dut1.require(PCIe(PCIeWidth.x2, on_board=False))
        dst_ep = self.dut2.require(PCIe(PCIeWidth.x2, on_board=False))

        topos = []

        # Apply constraints using constrain_topology context manager
        with constraint.constrain_topology(src_ep, dst_ep) as (src, dst):
            # Create TX path with blocking caps
            self.tx_couplers = []
            for i in range(len(src.data.lane)):
                tx_coupler = DiffPairCoupler(220.0e-9)
                self.tx_couplers.append(tx_coupler)

                # TX path: src.TX -> coupler.A -> coupler.B -> dst.TX
                # topo-pair equivalent using >> through the coupler
                topos.append([src.data.lane[i].TX >> tx_coupler.A])
                topos.append([tx_coupler.B >> dst.data.lane[i].TX])

            # RX path: straight through (no blocking caps)
            # topo-net equivalent
            for i in range(len(src.data.lane)):
                topos.append([src.data.lane[i].RX >> dst.data.lane[i].RX])

            # Reference clock - straight through
            if src.data.refclk is not None and dst.data.refclk is not None:
                topos.append([src.data.refclk >> dst.data.refclk])

            # Control signals - direct net connection (not topology)
            if src.control is not None and dst.control is not None:
                topos.append([src.control >> dst.control])
        return topos

    def _setup_ic_to_ic_connection(self, constraint: SignalConstraint[PCIe]):
        """Setup IC-to-IC PCIe connection

        Translation of the second constrain-topology block in pcie-main.stanza.

        For IC-to-IC connections (active to active):
        - Need null-modem style (TX->RX, RX->TX)
        - Blocking caps on both TX and RX paths
        - Use connect_pcie_crossover to handle the crossover
        """

        topos = []
        # Require x2 PCIe ports with PRSNT# from each device
        src_ic = self.dut1.require(PCIe(PCIeWidth.x2, on_board=False, prsnt=True))
        dst_ic = self.dut2.require(PCIe(PCIeWidth.x2, on_board=False, prsnt=True))

        # Apply constraints using constrain_topology context manager
        with constraint.constrain_topology(src_ic, dst_ic) as (src, dst_end):

            self.dummy_dst = PCIe(PCIeWidth.x2, on_board=False, prsnt=True)
            self.xover = connect_pcie_null_modem(dst_end, self.dummy_dst)

            # Use reverse_pcie_lanes for null-modem style connection
            # This swaps TX and RX so we can still use tx->tx and rx->rx syntax
            # self.dst_reversed = reverse_pcie_lanes(dst_end)
            dst = self.dummy_dst

            # Create TX path with blocking caps
            self.ic_tx_couplers = []
            for i in range(len(src.data.lane)):
                tx_coupler = DiffPairCoupler(220.0e-9)
                self.ic_tx_couplers.append(tx_coupler)

                # TX path: src.TX -> coupler -> dst.TX
                topos.append([src.data.lane[i].TX >> tx_coupler.A])
                topos.append([tx_coupler.B >> dst.data.lane[i].TX])

            # Create RX path with blocking caps (different from card edge)
            self.ic_rx_couplers = []
            for i in range(len(dst.data.lane)):
                rx_coupler = DiffPairCoupler(220.0e-9)
                self.ic_rx_couplers.append(rx_coupler)

                # RX path: dst.RX (really dst.TX)-> coupler -> src.RX
                topos.append([dst.data.lane[i].RX >> rx_coupler.B])
                topos.append([rx_coupler.A >> src.data.lane[i].RX])

            # Reference clock - straight through
            if src.data.refclk is not None and dst.data.refclk is not None:
                topos.append([src.data.refclk >> dst.data.refclk])

            # Control signals - direct net connection (not topology)
            if src.control is not None and dst.control is not None:
                topos.append([src.control >> dst.control])
        return topos


class PCIeExampleDesign(Design):
    """Complete PCIe Example Design

    Translation of design setup from pcie-main.stanza.
    """

    substrate = ExampleSubstrate()
    circuit = PCIeExampleCircuit()
    board = ExampleBoard()
