"""LPDDR4 Example Components

Translation of lpddr4_demo Stanza project to Python.
- Memory component: K4FBE3D4HB-KHCL Samsung LPDDR4 memory with direct port
- Controller component: Chip with Provide() for pin optionality

Based on:
- /Users/bgupta/src/JITX/customers/generic/lpddr4_demo/components/K4FBE3D4HB-KHCL.stanza
- /Users/bgupta/src/JITX/customers/generic/lpddr4_demo/components/chip.stanza
"""

from jitx import PadMapping, Provide
from jitx.circuit import Circuit
from jitx.component import Component
from jitx.common import Power
from jitx.net import DiffPair, Port

from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol

from ....protocols.memory.lpddr4 import LPDDR4, LPDDR4Width, LPDDR4Rank


class LPDDR4MemoryLandpattern(BGA):
    """22x12 BGA Landpattern for K4FBE3D4HB-KHCL LPDDR4 Memory.

    Based on Stanza lp-my-component:
    - 22 rows x 12 cols
    - Pitch: 0.8mm
    - Ball diameter: 0.41 * 0.75 = 0.3075mm
    """

    def __init__(self):
        super().__init__(
            num_rows=22,
            num_cols=12,
            ball_diameter=0.41 * 0.75,
            pitch=0.8,
        )
        self.pad_config(SMDPadConfig(copper=-0.05))


class K4FBE3D4HB_KHCL(Component):
    """Samsung K4FBE3D4HB-KHCL LPDDR4 Memory Component.

    Exact translation from lpddr4_demo/components/K4FBE3D4HB-KHCL.stanza.
    22x12 BGA with x32 LPDDR4 interface (2 x16 channels labeled _a and _b).
    """

    reference_prefix = "U"
    mpn = "K4FBE3D4HB-KHCL"
    manufacturer = "Samsung"
    description = "LPDDR4 memory"

    # Channel A (x16) - Data (16 bits)
    DQ_a = [Port() for _ in range(16)]

    # Channel B (x16) - Data (16 bits)
    DQ_b = [Port() for _ in range(16)]

    # Channel A - Data Strobes (2 differential pairs)
    DQS_t_a = [Port() for _ in range(2)]
    DQS_c_a = [Port() for _ in range(2)]

    # Channel B - Data Strobes (2 differential pairs)
    DQS_t_b = [Port() for _ in range(2)]
    DQS_c_b = [Port() for _ in range(2)]

    # Channel A - Data Mask (2 per channel)
    DMI_a = [Port() for _ in range(2)]

    # Channel B - Data Mask (2 per channel)
    DMI_b = [Port() for _ in range(2)]

    # Channel A - Clock (differential)
    CK_t_a = Port()
    CK_c_a = Port()

    # Channel B - Clock (differential)
    CK_t_b = Port()
    CK_c_b = Port()

    # Channel A - Command/Address (6 bits)
    CA_a = [Port() for _ in range(6)]

    # Channel B - Command/Address (6 bits)
    CA_b = [Port() for _ in range(6)]

    # Channel A - Control (2 CKE, 2 CS for dual rank)
    CKE_a = [Port() for _ in range(2)]
    CS_a = [Port() for _ in range(2)]

    # Channel B - Control (2 CKE, 2 CS for dual rank)
    CKE_b = [Port() for _ in range(2)]
    CS_b = [Port() for _ in range(2)]

    # Other signals
    ODT_CA_a = Port()
    ODT_CA_b = Port()
    RESET_n = Port()

    # Power
    VDD1 = [Port() for _ in range(8)]
    VDD2 = [Port() for _ in range(24)]
    VDDQ = [Port() for _ in range(20)]
    VSS = [Port() for _ in range(58)]
    ZQ = [Port() for _ in range(2)]

    landpattern = LPDDR4MemoryLandpattern()
    symbol = BoxSymbol()

    # Exact pad mapping from Stanza K4FBE3D4HB-KHCL.stanza
    mapping = [
        PadMapping(
            {
                # Channel A - CA
                CA_a[0]: landpattern.H[2],
                CA_a[1]: landpattern.J[2],
                CA_a[2]: landpattern.H[9],
                CA_a[3]: landpattern.H[10],
                CA_a[4]: landpattern.H[11],
                CA_a[5]: landpattern.J[11],
                # Channel B - CA
                CA_b[0]: landpattern.R[2],
                CA_b[1]: landpattern.P[2],
                CA_b[2]: landpattern.R[9],
                CA_b[3]: landpattern.R[10],
                CA_b[4]: landpattern.R[11],
                CA_b[5]: landpattern.P[11],
                # Channel A - Clock
                CK_c_a: landpattern.J[9],
                CK_t_a: landpattern.J[8],
                # Channel B - Clock
                CK_c_b: landpattern.P[9],
                CK_t_b: landpattern.P[8],
                # Channel A - Control
                CKE_a[0]: landpattern.J[4],
                CKE_a[1]: landpattern.J[5],
                CS_a[0]: landpattern.H[4],
                CS_a[1]: landpattern.H[3],
                # Channel B - Control
                CKE_b[0]: landpattern.P[4],
                CKE_b[1]: landpattern.P[5],
                CS_b[0]: landpattern.R[4],
                CS_b[1]: landpattern.R[3],
                # Channel A - DMI
                DMI_a[0]: landpattern.C[3],
                DMI_a[1]: landpattern.C[10],
                # Channel B - DMI
                DMI_b[0]: landpattern.Y[3],
                DMI_b[1]: landpattern.Y[10],
                # Channel A - DQ (byte 0: DQ0-7)
                DQ_a[0]: landpattern.B[2],
                DQ_a[1]: landpattern.C[2],
                DQ_a[2]: landpattern.E[2],
                DQ_a[3]: landpattern.F[2],
                DQ_a[4]: landpattern.F[4],
                DQ_a[5]: landpattern.E[4],
                DQ_a[6]: landpattern.C[4],
                DQ_a[7]: landpattern.B[4],
                # Channel A - DQ (byte 1: DQ8-15)
                DQ_a[8]: landpattern.B[11],
                DQ_a[9]: landpattern.C[11],
                DQ_a[10]: landpattern.E[11],
                DQ_a[11]: landpattern.F[11],
                DQ_a[12]: landpattern.F[9],
                DQ_a[13]: landpattern.E[9],
                DQ_a[14]: landpattern.C[9],
                DQ_a[15]: landpattern.B[9],
                # Channel B - DQ (byte 0: DQ0-7)
                DQ_b[0]: landpattern.AA[2],
                DQ_b[1]: landpattern.Y[2],
                DQ_b[2]: landpattern.V[2],
                DQ_b[3]: landpattern.U[2],
                DQ_b[4]: landpattern.U[4],
                DQ_b[5]: landpattern.V[4],
                DQ_b[6]: landpattern.Y[4],
                DQ_b[7]: landpattern.AA[4],
                # Channel B - DQ (byte 1: DQ8-15)
                DQ_b[8]: landpattern.AA[11],
                DQ_b[9]: landpattern.Y[11],
                DQ_b[10]: landpattern.V[11],
                DQ_b[11]: landpattern.U[11],
                DQ_b[12]: landpattern.U[9],
                DQ_b[13]: landpattern.V[9],
                DQ_b[14]: landpattern.Y[9],
                DQ_b[15]: landpattern.AA[9],
                # Channel A - DQS
                DQS_c_a[0]: landpattern.E[3],
                DQS_t_a[0]: landpattern.D[3],
                DQS_c_a[1]: landpattern.E[10],
                DQS_t_a[1]: landpattern.D[10],
                # Channel B - DQS
                DQS_c_b[0]: landpattern.V[3],
                DQS_t_b[0]: landpattern.W[3],
                DQS_c_b[1]: landpattern.V[10],
                DQS_t_b[1]: landpattern.W[10],
                # Other signals
                ODT_CA_a: landpattern.G[2],
                ODT_CA_b: landpattern.T[2],
                RESET_n: landpattern.T[11],
                # Power - VDD1 (8 pads)
                VDD1[0]: landpattern.F[1],
                VDD1[1]: landpattern.F[12],
                VDD1[2]: landpattern.G[4],
                VDD1[3]: landpattern.G[9],
                VDD1[4]: landpattern.T[4],
                VDD1[5]: landpattern.T[9],
                VDD1[6]: landpattern.U[1],
                VDD1[7]: landpattern.U[12],
                # Power - VDD2 (24 pads)
                VDD2[0]: landpattern.A[4],
                VDD2[1]: landpattern.A[9],
                VDD2[2]: landpattern.F[5],
                VDD2[3]: landpattern.F[8],
                VDD2[4]: landpattern.H[1],
                VDD2[5]: landpattern.H[5],
                VDD2[6]: landpattern.H[8],
                VDD2[7]: landpattern.H[12],
                VDD2[8]: landpattern.K[1],
                VDD2[9]: landpattern.K[3],
                VDD2[10]: landpattern.K[10],
                VDD2[11]: landpattern.K[12],
                VDD2[12]: landpattern.N[1],
                VDD2[13]: landpattern.N[3],
                VDD2[14]: landpattern.N[10],
                VDD2[15]: landpattern.N[12],
                VDD2[16]: landpattern.R[1],
                VDD2[17]: landpattern.R[5],
                VDD2[18]: landpattern.R[8],
                VDD2[19]: landpattern.R[12],
                VDD2[20]: landpattern.U[5],
                VDD2[21]: landpattern.U[8],
                VDD2[22]: landpattern.AB[4],
                VDD2[23]: landpattern.AB[9],
                # Power - VDDQ (20 pads)
                VDDQ[0]: landpattern.B[3],
                VDDQ[1]: landpattern.B[5],
                VDDQ[2]: landpattern.B[8],
                VDDQ[3]: landpattern.B[10],
                VDDQ[4]: landpattern.D[1],
                VDDQ[5]: landpattern.D[5],
                VDDQ[6]: landpattern.D[8],
                VDDQ[7]: landpattern.D[12],
                VDDQ[8]: landpattern.F[3],
                VDDQ[9]: landpattern.F[10],
                VDDQ[10]: landpattern.U[3],
                VDDQ[11]: landpattern.U[10],
                VDDQ[12]: landpattern.W[1],
                VDDQ[13]: landpattern.W[5],
                VDDQ[14]: landpattern.W[8],
                VDDQ[15]: landpattern.W[12],
                VDDQ[16]: landpattern.AA[3],
                VDDQ[17]: landpattern.AA[5],
                VDDQ[18]: landpattern.AA[8],
                VDDQ[19]: landpattern.AA[10],
                # Power - VSS (58 pads)
                VSS[0]: landpattern.A[3],
                VSS[1]: landpattern.A[10],
                VSS[2]: landpattern.C[1],
                VSS[3]: landpattern.C[5],
                VSS[4]: landpattern.C[8],
                VSS[5]: landpattern.C[12],
                VSS[6]: landpattern.D[2],
                VSS[7]: landpattern.D[4],
                VSS[8]: landpattern.D[9],
                VSS[9]: landpattern.D[11],
                VSS[10]: landpattern.E[1],
                VSS[11]: landpattern.E[5],
                VSS[12]: landpattern.E[8],
                VSS[13]: landpattern.E[12],
                VSS[14]: landpattern.G[1],
                VSS[15]: landpattern.G[3],
                VSS[16]: landpattern.G[5],
                VSS[17]: landpattern.G[8],
                VSS[18]: landpattern.G[10],
                VSS[19]: landpattern.G[12],
                VSS[20]: landpattern.J[1],
                VSS[21]: landpattern.J[3],
                VSS[22]: landpattern.J[10],
                VSS[23]: landpattern.J[12],
                VSS[24]: landpattern.K[2],
                VSS[25]: landpattern.K[4],
                VSS[26]: landpattern.K[9],
                VSS[27]: landpattern.K[11],
                VSS[28]: landpattern.N[2],
                VSS[29]: landpattern.N[4],
                VSS[30]: landpattern.N[9],
                VSS[31]: landpattern.N[11],
                VSS[32]: landpattern.P[1],
                VSS[33]: landpattern.P[3],
                VSS[34]: landpattern.P[10],
                VSS[35]: landpattern.P[12],
                VSS[36]: landpattern.T[1],
                VSS[37]: landpattern.T[3],
                VSS[38]: landpattern.T[5],
                VSS[39]: landpattern.T[8],
                VSS[40]: landpattern.T[10],
                VSS[41]: landpattern.T[12],
                VSS[42]: landpattern.V[1],
                VSS[43]: landpattern.V[5],
                VSS[44]: landpattern.V[8],
                VSS[45]: landpattern.V[12],
                VSS[46]: landpattern.W[2],
                VSS[47]: landpattern.W[4],
                VSS[48]: landpattern.W[9],
                VSS[49]: landpattern.W[11],
                VSS[50]: landpattern.Y[1],
                VSS[51]: landpattern.Y[5],
                VSS[52]: landpattern.Y[8],
                VSS[53]: landpattern.Y[12],
                VSS[54]: landpattern.AB[3],
                VSS[55]: landpattern.AB[5],
                VSS[56]: landpattern.AB[8],
                VSS[57]: landpattern.AB[10],
                # ZQ
                ZQ[0]: landpattern.A[5],
                ZQ[1]: landpattern.A[8],
            }
        )
    ]


class LPDDR4MemoryCircuit(Circuit):
    """LPDDR4 Memory Circuit with K4FBE3D4HB-KHCL.

    Direct LPDDR4 port (not Provide) for fixed pin connections.
    x32 configuration (2 x16 channels).
    """

    io = LPDDR4(LPDDR4Width.x32, LPDDR4Rank.Rank2)
    pwr = Power()

    def __init__(self):
        self.mem = K4FBE3D4HB_KHCL()

        topos = []

        # Channel 0 (channel A in memory) - Data Lane 0 (byte 0)
        for i in range(8):
            topos.append(self.io.ch[0].d[0].dq[i] >> self.mem.DQ_a[i])
        topos.append(self.io.ch[0].d[0].dqs.p >> self.mem.DQS_t_a[0])
        topos.append(self.io.ch[0].d[0].dqs.n >> self.mem.DQS_c_a[0])
        topos.append(self.io.ch[0].d[0].dmi >> self.mem.DMI_a[0])

        # Channel 0 - Data Lane 1 (byte 1)
        for i in range(8):
            topos.append(self.io.ch[0].d[1].dq[i] >> self.mem.DQ_a[8 + i])
        topos.append(self.io.ch[0].d[1].dqs.p >> self.mem.DQS_t_a[1])
        topos.append(self.io.ch[0].d[1].dqs.n >> self.mem.DQS_c_a[1])
        topos.append(self.io.ch[0].d[1].dmi >> self.mem.DMI_a[1])

        # Channel 0 - Clock and Control
        topos.append(self.io.ch[0].ck.p >> self.mem.CK_t_a)
        topos.append(self.io.ch[0].ck.n >> self.mem.CK_c_a)
        for i in range(6):
            topos.append(self.io.ch[0].ca[i] >> self.mem.CA_a[i])
        for i in range(2):
            topos.append(self.io.ch[0].cke[i] >> self.mem.CKE_a[i])
            topos.append(self.io.ch[0].cs[i] >> self.mem.CS_a[i])

        # Channel 1 (channel B in memory) - Data Lane 0 (byte 0)
        for i in range(8):
            topos.append(self.io.ch[1].d[0].dq[i] >> self.mem.DQ_b[i])
        topos.append(self.io.ch[1].d[0].dqs.p >> self.mem.DQS_t_b[0])
        topos.append(self.io.ch[1].d[0].dqs.n >> self.mem.DQS_c_b[0])
        topos.append(self.io.ch[1].d[0].dmi >> self.mem.DMI_b[0])

        # Channel 1 - Data Lane 1 (byte 1)
        for i in range(8):
            topos.append(self.io.ch[1].d[1].dq[i] >> self.mem.DQ_b[8 + i])
        topos.append(self.io.ch[1].d[1].dqs.p >> self.mem.DQS_t_b[1])
        topos.append(self.io.ch[1].d[1].dqs.n >> self.mem.DQS_c_b[1])
        topos.append(self.io.ch[1].d[1].dmi >> self.mem.DMI_b[1])

        # Channel 1 - Clock and Control
        topos.append(self.io.ch[1].ck.p >> self.mem.CK_t_b)
        topos.append(self.io.ch[1].ck.n >> self.mem.CK_c_b)
        for i in range(6):
            topos.append(self.io.ch[1].ca[i] >> self.mem.CA_b[i])
        for i in range(2):
            topos.append(self.io.ch[1].cke[i] >> self.mem.CKE_b[i])
            topos.append(self.io.ch[1].cs[i] >> self.mem.CS_b[i])

        self.topos = topos


class LPDDR4ControllerLandpattern(BGA):
    """22x22 BGA Landpattern for LPDDR4 Controller IC.

    Based on chip.stanza:
    - 22x22 = 484 balls
    - Pitch: 0.8mm
    - Ball diameter: 0.5mm
    """

    def __init__(self):
        super().__init__(
            num_rows=22,
            num_cols=22,
            ball_diameter=0.5,
            pitch=0.8,
        )
        self.pad_config(SMDPadConfig(copper=-0.05))


class LPDDR4ControllerComponent(Component):
    """LPDDR4 Controller/CPU Component.

    Translation from chip.stanza with 22x22 BGA.
    Has LPDDR4 interface pins that use Provide() for flexible pin assignment.
    """

    reference_prefix = "U"
    mpn = "JITX-LPDDR4-CPU"
    manufacturer = "JITX"
    description = "Example LPDDR4 Controller"

    # Power
    VDD_CPU = [Port() for _ in range(6)]
    GND = [Port() for _ in range(4)]

    # Data signals (32 total for x32)
    LP4_DQ = [Port() for _ in range(32)]

    # DQS pairs (4 differential pairs: 2 per channel)
    LP4_DQS_DP = [Port() for _ in range(4)]
    LP4_DQS_DN = [Port() for _ in range(4)]

    # Channel 0 - CA/Control
    LP4_0CA = [Port() for _ in range(6)]
    LP4_0CKE = [Port() for _ in range(2)]
    LP4_0CLK_DP = Port()
    LP4_0CLK_DN = Port()
    LP4_0CS = [Port() for _ in range(2)]

    # Channel 1 - CA/Control
    LP4_1CA = [Port() for _ in range(6)]
    LP4_1CKE = [Port() for _ in range(2)]
    LP4_1CLK_DP = Port()
    LP4_1CLK_DN = Port()
    LP4_1CS = [Port() for _ in range(2)]

    # DMI signals (4 total: 2 per channel)
    LP4_DMI = [Port() for _ in range(4)]

    landpattern = LPDDR4ControllerLandpattern()
    symbol = BoxSymbol()

    # Pad mapping from chip.stanza
    mapping = [
        PadMapping(
            {
                # Power
                VDD_CPU[0]: landpattern.N[4],
                VDD_CPU[1]: landpattern.P[4],
                VDD_CPU[2]: landpattern.R[4],
                VDD_CPU[3]: landpattern.T[4],
                VDD_CPU[4]: landpattern.U[4],
                VDD_CPU[5]: landpattern.V[4],
                GND[0]: landpattern.A[1],
                GND[1]: landpattern.A[2],
                GND[2]: landpattern.A[3],
                GND[3]: landpattern.AB[1],
                # Channel 0 DQ (0-15)
                LP4_DQ[0]: landpattern.B[1],
                LP4_DQ[1]: landpattern.B[2],
                LP4_DQ[2]: landpattern.B[3],
                LP4_DQ[3]: landpattern.C[2],
                LP4_DQ[4]: landpattern.D[2],
                LP4_DQ[5]: landpattern.E[1],
                LP4_DQ[6]: landpattern.E[2],
                LP4_DQ[7]: landpattern.E[3],
                LP4_DQ[8]: landpattern.F[1],
                LP4_DQ[9]: landpattern.F[2],
                LP4_DQ[10]: landpattern.F[3],
                LP4_DQ[11]: landpattern.G[2],
                LP4_DQ[12]: landpattern.H[2],
                LP4_DQ[13]: landpattern.J[1],
                LP4_DQ[14]: landpattern.J[2],
                LP4_DQ[15]: landpattern.J[3],
                # Channel 1 DQ (16-31)
                LP4_DQ[16]: landpattern.P[1],
                LP4_DQ[17]: landpattern.P[2],
                LP4_DQ[18]: landpattern.P[3],
                LP4_DQ[19]: landpattern.R[2],
                LP4_DQ[20]: landpattern.T[5],
                LP4_DQ[21]: landpattern.U[1],
                LP4_DQ[22]: landpattern.U[2],
                LP4_DQ[23]: landpattern.T[3],
                LP4_DQ[24]: landpattern.U[3],
                LP4_DQ[25]: landpattern.V[2],
                LP4_DQ[26]: landpattern.V[3],
                LP4_DQ[27]: landpattern.W[2],
                LP4_DQ[28]: landpattern.W[3],
                LP4_DQ[29]: landpattern.Y[1],
                LP4_DQ[30]: landpattern.Y[2],
                LP4_DQ[31]: landpattern.T[2],
                # DQS pairs
                LP4_DQS_DN[0]: landpattern.C[1],
                LP4_DQS_DP[0]: landpattern.D[1],
                LP4_DQS_DN[1]: landpattern.G[1],
                LP4_DQS_DP[1]: landpattern.H[1],
                LP4_DQS_DN[2]: landpattern.T[1],
                LP4_DQS_DP[2]: landpattern.R[1],
                LP4_DQS_DN[3]: landpattern.W[1],
                LP4_DQS_DP[3]: landpattern.V[1],
                # Channel 0 - CA/Control
                LP4_0CA[0]: landpattern.C[3],
                LP4_0CA[1]: landpattern.D[3],
                LP4_0CA[2]: landpattern.G[3],
                LP4_0CA[3]: landpattern.H[3],
                LP4_0CA[4]: landpattern.N[3],
                LP4_0CA[5]: landpattern.R[3],
                LP4_0CKE[0]: landpattern.K[1],
                LP4_0CKE[1]: landpattern.N[1],
                LP4_0CLK_DN: landpattern.L[1],
                LP4_0CLK_DP: landpattern.M[1],
                LP4_0CS[0]: landpattern.N[2],
                LP4_0CS[1]: landpattern.AA[3],
                # Channel 1 - CA/Control
                LP4_1CA[0]: landpattern.C[5],
                LP4_1CA[1]: landpattern.D[5],
                LP4_1CA[2]: landpattern.G[5],
                LP4_1CA[3]: landpattern.H[5],
                LP4_1CA[4]: landpattern.N[5],
                LP4_1CA[5]: landpattern.R[5],
                LP4_1CKE[0]: landpattern.K[6],
                LP4_1CKE[1]: landpattern.N[6],
                LP4_1CLK_DN: landpattern.L[6],
                LP4_1CLK_DP: landpattern.M[6],
                LP4_1CS[0]: landpattern.N[7],
                LP4_1CS[1]: landpattern.AA[4],
                # DMI signals (use arbitrary pads since Stanza didn't map these)
                LP4_DMI[0]: landpattern.AA[5],
                LP4_DMI[1]: landpattern.AA[6],
                LP4_DMI[2]: landpattern.AA[7],
                LP4_DMI[3]: landpattern.AA[8],
            }
        )
    ]


class LPDDR4ControllerCircuit(Circuit):
    """LPDDR4 Controller Circuit with Provide() for pin optionality.

    Uses Provide() to allow flexible pin assignment from the controller component.
    """

    pwr = Power()

    def __init__(self):
        self.cpu = LPDDR4ControllerComponent()

        # Use Provide for LPDDR4 interface with pin optionality
        # The lambda receives the bundle and returns a list with the mapping dict
        self._lpddr4_provide = Provide(LPDDR4(LPDDR4Width.x32, LPDDR4Rank.Rank2)).one_of(
            lambda b: [self._create_lpddr4_mapping(b)]
        )

    def _create_lpddr4_mapping(self, b: LPDDR4) -> dict:
        """Create the LPDDR4 bundle to component pin mapping."""
        mapping = {}

        # Channel 0 - Data Lane 0 (DQ 0-7)
        for i in range(8):
            mapping[b.ch[0].d[0].dq[i]] = self.cpu.LP4_DQ[i]
        mapping[b.ch[0].d[0].dqs.p] = self.cpu.LP4_DQS_DP[0]
        mapping[b.ch[0].d[0].dqs.n] = self.cpu.LP4_DQS_DN[0]
        mapping[b.ch[0].d[0].dmi] = self.cpu.LP4_DMI[0]

        # Channel 0 - Data Lane 1 (DQ 8-15)
        for i in range(8):
            mapping[b.ch[0].d[1].dq[i]] = self.cpu.LP4_DQ[8 + i]
        mapping[b.ch[0].d[1].dqs.p] = self.cpu.LP4_DQS_DP[1]
        mapping[b.ch[0].d[1].dqs.n] = self.cpu.LP4_DQS_DN[1]
        mapping[b.ch[0].d[1].dmi] = self.cpu.LP4_DMI[1]

        # Channel 0 - Clock and Control
        mapping[b.ch[0].ck.p] = self.cpu.LP4_0CLK_DP
        mapping[b.ch[0].ck.n] = self.cpu.LP4_0CLK_DN
        for i in range(6):
            mapping[b.ch[0].ca[i]] = self.cpu.LP4_0CA[i]
        for i in range(2):
            mapping[b.ch[0].cke[i]] = self.cpu.LP4_0CKE[i]
            mapping[b.ch[0].cs[i]] = self.cpu.LP4_0CS[i]

        # Channel 1 - Data Lane 0 (DQ 16-23)
        for i in range(8):
            mapping[b.ch[1].d[0].dq[i]] = self.cpu.LP4_DQ[16 + i]
        mapping[b.ch[1].d[0].dqs.p] = self.cpu.LP4_DQS_DP[2]
        mapping[b.ch[1].d[0].dqs.n] = self.cpu.LP4_DQS_DN[2]
        mapping[b.ch[1].d[0].dmi] = self.cpu.LP4_DMI[2]

        # Channel 1 - Data Lane 1 (DQ 24-31)
        for i in range(8):
            mapping[b.ch[1].d[1].dq[i]] = self.cpu.LP4_DQ[24 + i]
        mapping[b.ch[1].d[1].dqs.p] = self.cpu.LP4_DQS_DP[3]
        mapping[b.ch[1].d[1].dqs.n] = self.cpu.LP4_DQS_DN[3]
        mapping[b.ch[1].d[1].dmi] = self.cpu.LP4_DMI[3]

        # Channel 1 - Clock and Control
        mapping[b.ch[1].ck.p] = self.cpu.LP4_1CLK_DP
        mapping[b.ch[1].ck.n] = self.cpu.LP4_1CLK_DN
        for i in range(6):
            mapping[b.ch[1].ca[i]] = self.cpu.LP4_1CA[i]
        for i in range(2):
            mapping[b.ch[1].cke[i]] = self.cpu.LP4_1CKE[i]
            mapping[b.ch[1].cs[i]] = self.cpu.LP4_1CS[i]

        return mapping
