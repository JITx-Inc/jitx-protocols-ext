"""DDR4 Example Components

DDR4 controller and dual-memory circuit with fly-by topology.
Component and single-chip circuit live in MT40A1G16TB_062E_F.py.
"""

from jitx import PadMapping
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.net import Port, Provide
from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol

from jitx_protocols_ext.protocols.memory.ddr4 import DDR4, DDR4Rank, DDR4Width

from .MT40A1G16TB_062E_F import (
    MT40A1G16TB_062E_F,
)

# Re-export for backward compatibility
DDR4MemoryComponent = MT40A1G16TB_062E_F


class DDR4MemoryCircuit(Circuit):
    """DDR4 Dual-Memory Circuit with Fly-by Topology

    Maps DDR4 bundle to dual MT40A1G16TB-062E-F memory components.
    Uses direct io port with >> topologies for fly-by signal chaining.

    DDR4 Fly-by topology:
    - Shared signals (fan out to both chips): DQ, DQS, DM_n, A, BA, ACT_n, RESET_n, PAR, ALERT_n
    - Per-chip signals: CK, CS_n, CKE, ODT, BG
    """

    io = DDR4(DDR4Width.x16, DDR4Rank.SingleRank)
    pwr = Power()
    pwr_q = Power()
    VPP = Port()
    VREFCA = Port()

    def __init__(self):
        self.mem0 = MT40A1G16TB_062E_F()
        self.mem1 = MT40A1G16TB_062E_F()

        # Power connections for both chips
        pwr_net = self.pwr.Vp
        for vdd in self.mem0.VDD:
            pwr_net = pwr_net + vdd
        for vdd in self.mem1.VDD:
            pwr_net = pwr_net + vdd
        self.vdd_net = pwr_net

        gnd_net = self.pwr.Vn
        for vss in self.mem0.VSS:
            gnd_net = gnd_net + vss
        for vss in self.mem1.VSS:
            gnd_net = gnd_net + vss
        self.vss_net = gnd_net

        vddq_net = self.pwr_q.Vp
        for vddq in self.mem0.VDDQ:
            vddq_net = vddq_net + vddq
        for vddq in self.mem1.VDDQ:
            vddq_net = vddq_net + vddq
        self.vddq_net = vddq_net

        vssq_net = self.pwr_q.Vn
        for vssq in self.mem0.VSSQ:
            vssq_net = vssq_net + vssq
        for vssq in self.mem1.VSSQ:
            vssq_net = vssq_net + vssq
        self.vssq_net = vssq_net

        vpp_net = self.VPP
        for vpp in self.mem0.VPP:
            vpp_net = vpp_net + vpp
        for vpp in self.mem1.VPP:
            vpp_net = vpp_net + vpp
        self.vpp_net = vpp_net

        self.vrefca_net = self.VREFCA + self.mem0.VREFCA + self.mem1.VREFCA

        # DDR4 Fly-by topology connections
        topos = []

        # DQ - shared, fan out to both memories (fly-by topology)
        for i in range(16):
            topos.append(self.io.data.DQ[i] >> self.mem0.DQ[i])
            topos.append(self.mem0.DQ[i] >> self.mem1.DQ[i])

        # DQS - shared differential pairs, fan out to both memories
        topos.append(self.io.data.DQS[0].p >> self.mem0.LDQS_P)
        topos.append(self.mem0.LDQS_P >> self.mem1.LDQS_P)
        topos.append(self.io.data.DQS[0].n >> self.mem0.LDQS_N)
        topos.append(self.mem0.LDQS_N >> self.mem1.LDQS_N)
        topos.append(self.io.data.DQS[1].p >> self.mem0.UDQS_P)
        topos.append(self.mem0.UDQS_P >> self.mem1.UDQS_P)
        topos.append(self.io.data.DQS[1].n >> self.mem0.UDQS_N)
        topos.append(self.mem0.UDQS_N >> self.mem1.UDQS_N)

        # DM_n - shared, fan out to both memories
        topos.append(self.io.data.DM_n[0] >> self.mem0.LDM_N)
        topos.append(self.mem0.LDM_N >> self.mem1.LDM_N)
        topos.append(self.io.data.DM_n[1] >> self.mem0.UDM_N)
        topos.append(self.mem0.UDM_N >> self.mem1.UDM_N)

        # Address - shared, fan out to both memories
        for i in range(17):
            topos.append(self.io.acc.A[i] >> self.mem0.A[i])
            topos.append(self.mem0.A[i] >> self.mem1.A[i])

        # Bank address - shared, fan out to both memories
        for i in range(2):
            topos.append(self.io.acc.BA[i] >> self.mem0.BA[i])
            topos.append(self.mem0.BA[i] >> self.mem1.BA[i])

        # Bank group - per-chip (x16 only has 1 BG per chip)
        topos.append(self.io.acc.BG[0] >> self.mem0.BG[0])
        topos.append(self.io.acc.BG[1] >> self.mem1.BG[0])

        # CK - per-chip differential pairs
        topos.append(self.io.acc.CK[0].p >> self.mem0.CK_P)
        topos.append(self.io.acc.CK[0].n >> self.mem0.CK_N)
        topos.append(self.io.acc.CK[1].p >> self.mem1.CK_P)
        topos.append(self.io.acc.CK[1].n >> self.mem1.CK_N)

        # Control signals - per-chip
        topos.append(self.io.acc.CKE[0] >> self.mem0.CKE)
        topos.append(self.io.acc.CS_n[0] >> self.mem0.CS_N)
        topos.append(self.io.acc.ODT[0] >> self.mem0.ODT)

        # Second chip control signals (if bundle supports dual rank)
        if len(self.io.acc.CKE) > 1:
            topos.append(self.io.acc.CKE[1] >> self.mem1.CKE)
        if len(self.io.acc.CS_n) > 1:
            topos.append(self.io.acc.CS_n[1] >> self.mem1.CS_N)
        if len(self.io.acc.ODT) > 1:
            topos.append(self.io.acc.ODT[1] >> self.mem1.ODT)

        # Shared control signals - fan out to both memories
        topos.append(self.io.acc.ACT_n >> self.mem0.ACT_N)
        topos.append(self.mem0.ACT_N >> self.mem1.ACT_N)
        topos.append(self.io.acc.RESET_n >> self.mem0.RESET_N)
        topos.append(self.mem0.RESET_N >> self.mem1.RESET_N)
        topos.append(self.io.acc.PAR >> self.mem0.PAR)
        topos.append(self.mem0.PAR >> self.mem1.PAR)
        topos.append(self.io.acc.ALERT_n >> self.mem0.ALERT_N)
        topos.append(self.mem0.ALERT_N >> self.mem1.ALERT_N)

        self.topos = topos


class DDR4ControllerBGALandpattern(BGA):
    """BGA Landpattern for DDR4 Controller Component

    Standard BGA for controller/SoC side.
    """

    def __init__(self):
        super().__init__(
            num_rows=20,
            num_cols=20,
            ball_diameter=0.40,
            pitch=0.65,
        )
        self.pad_config(SMDPadConfig())
        self.density_level(DensityLevel.B)


class DDR4ControllerComponent(Component):
    """DDR4 Controller Component

    Controller/SoC component with DDR4 interface pins.
    """

    reference_prefix = "U"
    mpn = "JITX-DDR4-CTRL"
    description = "Dummy DDR4 controller"

    # Same signal interface as memory
    DQ = [Port() for _ in range(16)]
    DQS_P = [Port() for _ in range(2)]
    DQS_N = [Port() for _ in range(2)]
    DM_N = [Port() for _ in range(2)]
    CK_P = Port()
    CK_N = Port()
    A = [Port() for _ in range(17)]
    BA = [Port() for _ in range(2)]
    BG = [Port() for _ in range(1)]
    CKE = Port()
    CS_N = Port()
    ODT = Port()
    ACT_N = Port()
    RESET_N = Port()
    PAR = Port()
    ALERT_N = Port()
    VDD = [Port() for _ in range(10)]
    VSS = [Port() for _ in range(40)]
    VDDQ = [Port() for _ in range(8)]

    landpattern = DDR4ControllerBGALandpattern()
    symbol = BoxSymbol()


# Reduced alphabet for BGA row naming (no I, O, Q, S, X, Z per JEDEC)
_CTRL_REDUCED_ALPHA = "ABCDEFGHJKLMNPRTUVWY"


def _ctrl_row_name(idx: int) -> str:
    """Convert row index to BGA row name using JEDEC reduced alphabet."""
    if idx < len(_CTRL_REDUCED_ALPHA):
        return _CTRL_REDUCED_ALPHA[idx]
    first = idx // len(_CTRL_REDUCED_ALPHA) - 1
    second = idx % len(_CTRL_REDUCED_ALPHA)
    return _CTRL_REDUCED_ALPHA[first] + _CTRL_REDUCED_ALPHA[second]


def _generate_ctrl_mapping():
    """Generate pad mapping for DDR4 controller (20x20 BGA)."""
    lp = DDR4ControllerComponent.landpattern
    pad_map = {}
    pad_idx = 0

    # Map all signal pins to pads
    all_ports = []

    # Collect all ports to map
    for dq in DDR4ControllerComponent.DQ:
        all_ports.append(dq)
    for dqs_p in DDR4ControllerComponent.DQS_P:
        all_ports.append(dqs_p)
    for dqs_n in DDR4ControllerComponent.DQS_N:
        all_ports.append(dqs_n)
    for dm_n in DDR4ControllerComponent.DM_N:
        all_ports.append(dm_n)
    all_ports.append(DDR4ControllerComponent.CK_P)
    all_ports.append(DDR4ControllerComponent.CK_N)
    for a in DDR4ControllerComponent.A:
        all_ports.append(a)
    for ba in DDR4ControllerComponent.BA:
        all_ports.append(ba)
    for bg in DDR4ControllerComponent.BG:
        all_ports.append(bg)
    all_ports.append(DDR4ControllerComponent.CKE)
    all_ports.append(DDR4ControllerComponent.CS_N)
    all_ports.append(DDR4ControllerComponent.ODT)
    all_ports.append(DDR4ControllerComponent.ACT_N)
    all_ports.append(DDR4ControllerComponent.RESET_N)
    all_ports.append(DDR4ControllerComponent.PAR)
    all_ports.append(DDR4ControllerComponent.ALERT_N)
    for vdd in DDR4ControllerComponent.VDD:
        all_ports.append(vdd)
    for vss in DDR4ControllerComponent.VSS:
        all_ports.append(vss)
    for vddq in DDR4ControllerComponent.VDDQ:
        all_ports.append(vddq)

    # Map ports to pads sequentially
    for row in range(20):
        row_letter = _ctrl_row_name(row)
        for col in range(20):
            col_num = col + 1
            if pad_idx < len(all_ports):
                pad_ref = getattr(lp, row_letter)[col_num]
                pad_map[all_ports[pad_idx]] = pad_ref
                pad_idx += 1

    return pad_map


# Build the controller mapping after class definition
DDR4ControllerComponent.mapping = [PadMapping(_generate_ctrl_mapping())]


class DDR4ControllerComponent2(Component):
    """DDR4 Controller Component with full signal set

    Controller/SoC component with DDR4 interface pins supporting 2 BG and 2 CK.
    """

    reference_prefix = "U"
    mpn = "JITX-DDR4-CTRL2"
    description = "Dummy DDR4 controller with dual rank support"

    # Data signals
    DQ = [Port() for _ in range(16)]
    DQS_P = [Port() for _ in range(2)]
    DQS_N = [Port() for _ in range(2)]
    DM_N = [Port() for _ in range(2)]

    # Clock - 2 pairs for dual rank
    CK_P = [Port() for _ in range(2)]
    CK_N = [Port() for _ in range(2)]

    # Address and bank
    A = [Port() for _ in range(17)]
    BA = [Port() for _ in range(2)]
    BG = [Port() for _ in range(2)]  # 2 BG signals

    # Control signals - 2 each for dual rank
    CKE = [Port() for _ in range(2)]
    CS_N = [Port() for _ in range(2)]
    ODT = [Port() for _ in range(2)]
    ACT_N = Port()
    RESET_N = Port()
    PAR = Port()
    ALERT_N = Port()

    # Power
    VDD = [Port() for _ in range(10)]
    VSS = [Port() for _ in range(40)]
    VDDQ = [Port() for _ in range(8)]

    landpattern = DDR4ControllerBGALandpattern()
    symbol = BoxSymbol()


def _generate_ctrl2_mapping():
    """Generate pad mapping for DDR4 controller 2 (20x20 BGA)."""
    lp = DDR4ControllerComponent2.landpattern
    pad_map = {}
    pad_idx = 0

    # Collect all ports to map
    all_ports = []
    for dq in DDR4ControllerComponent2.DQ:
        all_ports.append(dq)
    for dqs_p in DDR4ControllerComponent2.DQS_P:
        all_ports.append(dqs_p)
    for dqs_n in DDR4ControllerComponent2.DQS_N:
        all_ports.append(dqs_n)
    for dm_n in DDR4ControllerComponent2.DM_N:
        all_ports.append(dm_n)
    for ck_p in DDR4ControllerComponent2.CK_P:
        all_ports.append(ck_p)
    for ck_n in DDR4ControllerComponent2.CK_N:
        all_ports.append(ck_n)
    for a in DDR4ControllerComponent2.A:
        all_ports.append(a)
    for ba in DDR4ControllerComponent2.BA:
        all_ports.append(ba)
    for bg in DDR4ControllerComponent2.BG:
        all_ports.append(bg)
    for cke in DDR4ControllerComponent2.CKE:
        all_ports.append(cke)
    for cs_n in DDR4ControllerComponent2.CS_N:
        all_ports.append(cs_n)
    for odt in DDR4ControllerComponent2.ODT:
        all_ports.append(odt)
    all_ports.append(DDR4ControllerComponent2.ACT_N)
    all_ports.append(DDR4ControllerComponent2.RESET_N)
    all_ports.append(DDR4ControllerComponent2.PAR)
    all_ports.append(DDR4ControllerComponent2.ALERT_N)
    for vdd in DDR4ControllerComponent2.VDD:
        all_ports.append(vdd)
    for vss in DDR4ControllerComponent2.VSS:
        all_ports.append(vss)
    for vddq in DDR4ControllerComponent2.VDDQ:
        all_ports.append(vddq)

    # Map ports to pads sequentially
    for row in range(20):
        row_letter = _ctrl_row_name(row)
        for col in range(20):
            col_num = col + 1
            if pad_idx < len(all_ports):
                pad_ref = getattr(lp, row_letter)[col_num]
                pad_map[all_ports[pad_idx]] = pad_ref
                pad_idx += 1

    return pad_map


DDR4ControllerComponent2.mapping = [PadMapping(_generate_ctrl2_mapping())]


class DDR4ControllerCircuit(Circuit):
    """DDR4 Controller Circuit

    Maps DDR4 bundle to controller component pins with full signal support.
    Uses Provide pattern for proper connectivity (equivalent to Stanza's supports).
    """

    pwr = Power()

    def __init__(self):
        self.ctrl = DDR4ControllerComponent2()

        # Provide a DDR4 interface with default parameters (2 CK, 2 BG)
        self.ddr4_provide = Provide(DDR4(DDR4Width.x16, DDR4Rank.SingleRank)).one_of(
            lambda b: [self._create_ddr4_mapping(b)]
        )

    def _create_ddr4_mapping(self, b: DDR4) -> dict:
        """Create mapping from DDR4 bundle signals to controller component pins."""
        mapping = {}

        # DQ mapping
        for i in range(16):
            mapping[b.data.DQ[i]] = self.ctrl.DQ[i]

        # DQS mapping
        mapping[b.data.DQS[0].p] = self.ctrl.DQS_P[0]
        mapping[b.data.DQS[0].n] = self.ctrl.DQS_N[0]
        mapping[b.data.DQS[1].p] = self.ctrl.DQS_P[1]
        mapping[b.data.DQS[1].n] = self.ctrl.DQS_N[1]

        # DM_n mapping
        mapping[b.data.DM_n[0]] = self.ctrl.DM_N[0]
        mapping[b.data.DM_n[1]] = self.ctrl.DM_N[1]

        # Address mapping
        for i in range(17):
            mapping[b.acc.A[i]] = self.ctrl.A[i]

        # Bank address mapping
        for i in range(2):
            mapping[b.acc.BA[i]] = self.ctrl.BA[i]

        # Bank group - 2 BG signals
        mapping[b.acc.BG[0]] = self.ctrl.BG[0]
        mapping[b.acc.BG[1]] = self.ctrl.BG[1]

        # Clock - 2 CK pairs
        mapping[b.acc.CK[0].p] = self.ctrl.CK_P[0]
        mapping[b.acc.CK[0].n] = self.ctrl.CK_N[0]
        mapping[b.acc.CK[1].p] = self.ctrl.CK_P[1]
        mapping[b.acc.CK[1].n] = self.ctrl.CK_N[1]

        # Control signals - 2 each for dual rank support
        mapping[b.acc.CKE[0]] = self.ctrl.CKE[0]
        mapping[b.acc.CS_n[0]] = self.ctrl.CS_N[0]
        mapping[b.acc.ODT[0]] = self.ctrl.ODT[0]

        if len(b.acc.CKE) > 1:
            mapping[b.acc.CKE[1]] = self.ctrl.CKE[1]
        if len(b.acc.CS_n) > 1:
            mapping[b.acc.CS_n[1]] = self.ctrl.CS_N[1]
        if len(b.acc.ODT) > 1:
            mapping[b.acc.ODT[1]] = self.ctrl.ODT[1]

        # Shared control signals
        mapping[b.acc.ACT_n] = self.ctrl.ACT_N
        mapping[b.acc.RESET_n] = self.ctrl.RESET_N
        mapping[b.acc.PAR] = self.ctrl.PAR
        mapping[b.acc.ALERT_n] = self.ctrl.ALERT_N

        return mapping
