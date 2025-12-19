"""Micron MT62F4G32D8DV-026_AIT_B LPDDR5X Memory Component

Translation of /Users/bgupta/src/JITX/customers/lockheed-martin/tssr-parts/parts/components/MT62F4G32D8DV-026_AIT_B.stanza

16GB LPDDR5X SDRAM, 7500Mbps, 315-ball LFBGA, Automotive Grade
"""

from jitx import PadMapping
from jitx.circuit import Circuit
from jitx.component import Component
from jitx.common import Power
from jitx.net import Port
from jitx.toleranced import Toleranced

from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol

from ....protocols.memory.lpddr5 import LPDDR5, LPDDR5Width, LPDDR5Rank


class MT62F4G32D8DVLandpattern(BGA):
    """315-ball LFBGA Landpattern for MT62F4G32D8DV-026_AIT_B

    Package specifications from Micron datasheet:
    - 315-ball LFBGA (21 rows x 15 columns)
    - 0.8mm pitch
    - 0.475mm ball diameter
    - Package body: 15.0mm x 12.4mm x 1.3mm max
    - Density level B
    """

    def __init__(self):
        super().__init__(
            num_rows=21,
            num_cols=15,
            ball_diameter=0.475,
            pitch=0.8,
        )
        self.pad_config(SMDPadConfig())
        self.package_body(
            RectanglePackage(
                width=Toleranced(15.0, 0.1),
                length=Toleranced(12.4, 0.1),
                height=Toleranced(1.3, 0.1),
            )
        )
        self.density_level(DensityLevel.B)


class MT62F4G32D8DV_026_AIT_B(Component):
    """Micron MT62F4G32D8DV-026_AIT_B LPDDR5X Memory Component

    16GB LPDDR5X SDRAM, 7500Mbps, 315-ball LFBGA, Automotive Grade

    Pin configuration:
    - Channel A: DQ[16], WCK[4], RDQS[4], DMI[2], CK[2], CS[2], CA[7]
    - Channel B: DQ[16], WCK[4], RDQS[4], DMI[2], CK[2], CS[2], CA[7]
    - Control: RESET_N, ZQ_A
    - Power: VDD1[4], VDD2H[61], VDD2L[16], VDDQ[40], VSS[102]
    """

    reference_prefix = "U"
    mpn = "MT62F4G32D8DV-026:B"
    manufacturer = "Micron Technology"
    description = "16GB LPDDR5X SDRAM, 7500Mbps, 315-ball LFBGA, Automotive Grade"

    # Channel A Data (16 bits = 2 lanes x 8 bits)
    DQ_A = [Port() for _ in range(16)]

    # Channel B Data (16 bits = 2 lanes x 8 bits)
    DQ_B = [Port() for _ in range(16)]

    # Write Clock - Channel A (2 diff pairs = 4 pins)
    WCK_t_A = [Port() for _ in range(2)]
    WCK_c_A = [Port() for _ in range(2)]

    # Write Clock - Channel B (2 diff pairs = 4 pins)
    WCK_t_B = [Port() for _ in range(2)]
    WCK_c_B = [Port() for _ in range(2)]

    # Read Data Strobe - Channel A (2 diff pairs = 4 pins)
    RDQS_t_A = [Port() for _ in range(2)]
    RDQS_c_A = [Port() for _ in range(2)]

    # Read Data Strobe - Channel B (2 diff pairs = 4 pins)
    RDQS_t_B = [Port() for _ in range(2)]
    RDQS_c_B = [Port() for _ in range(2)]

    # Data Mask - Channel A (2 pins, one per lane)
    DMI_A = [Port() for _ in range(2)]

    # Data Mask - Channel B (2 pins, one per lane)
    DMI_B = [Port() for _ in range(2)]

    # Clock - Channel A (1 diff pair)
    CK_t_A = Port()
    CK_c_A = Port()

    # Clock - Channel B (1 diff pair)
    CK_t_B = Port()
    CK_c_B = Port()

    # Chip Select - Channel A (2 ranks)
    CS_A = [Port() for _ in range(2)]

    # Chip Select - Channel B (2 ranks)
    CS_B = [Port() for _ in range(2)]

    # Command/Address - Channel A (7 bits)
    CA_A = [Port() for _ in range(7)]

    # Command/Address - Channel B (7 bits)
    CA_B = [Port() for _ in range(7)]

    # Control
    RESET_N = Port()
    ZQ_A = Port()

    # Power - VDD1 (4 pins)
    VDD1 = [Port() for _ in range(4)]

    # Power - VDD2H (61 pins)
    VDD2H = [Port() for _ in range(61)]

    # Power - VDD2L (16 pins)
    VDD2L = [Port() for _ in range(16)]

    # Power - VDDQ (40 pins)
    VDDQ = [Port() for _ in range(40)]

    # Ground - VSS (102 pins)
    VSS = [Port() for _ in range(102)]

    # No Connect and Reserved (not mapped to bundle)
    NC = [Port() for _ in range(12)]
    RFU = [Port() for _ in range(4)]

    landpattern = MT62F4G32D8DVLandpattern()
    symbol = BoxSymbol()

    # Pad mapping based on Micron datasheet pinout (21x15 BGA)
    mapping = [
        PadMapping(
            {
                # Row A (15 balls)
                NC[0]: landpattern.A[1],
                NC[1]: landpattern.A[2],
                VDDQ[0]: landpattern.A[3],
                DMI_A[0]: landpattern.A[4],
                VSS[0]: landpattern.A[5],
                VDD2L[0]: landpattern.A[6],
                VDD2H[0]: landpattern.A[7],
                VDD2H[1]: landpattern.A[8],
                VDD2H[2]: landpattern.A[9],
                VDD2L[1]: landpattern.A[10],
                VSS[1]: landpattern.A[11],
                DMI_A[1]: landpattern.A[12],
                VDDQ[1]: landpattern.A[13],
                NC[2]: landpattern.A[14],
                NC[3]: landpattern.A[15],
                # Row B
                NC[4]: landpattern.B[1],
                VDDQ[2]: landpattern.B[2],
                RDQS_t_A[0]: landpattern.B[3],
                VSS[2]: landpattern.B[4],
                DQ_A[4]: landpattern.B[5],
                VDD2L[2]: landpattern.B[6],
                VDD2H[3]: landpattern.B[7],
                VSS[3]: landpattern.B[8],
                VDD2H[4]: landpattern.B[9],
                VDD2L[3]: landpattern.B[10],
                DQ_A[12]: landpattern.B[11],
                VSS[4]: landpattern.B[12],
                RDQS_t_A[1]: landpattern.B[13],
                VDDQ[3]: landpattern.B[14],
                NC[5]: landpattern.B[15],
                # Row C
                VDD1[0]: landpattern.C[1],
                DQ_A[1]: landpattern.C[2],
                VDDQ[4]: landpattern.C[3],
                RDQS_c_A[0]: landpattern.C[4],
                VSS[5]: landpattern.C[5],
                DQ_A[5]: landpattern.C[6],
                VDD2H[5]: landpattern.C[7],
                VSS[6]: landpattern.C[8],
                VDD2H[6]: landpattern.C[9],
                DQ_A[13]: landpattern.C[10],
                VSS[7]: landpattern.C[11],
                RDQS_c_A[1]: landpattern.C[12],
                VDDQ[5]: landpattern.C[13],
                DQ_A[9]: landpattern.C[14],
                VDD1[1]: landpattern.C[15],
                # Row D
                DQ_A[0]: landpattern.D[1],
                VSS[8]: landpattern.D[2],
                DQ_A[3]: landpattern.D[3],
                VDDQ[6]: landpattern.D[4],
                WCK_c_A[0]: landpattern.D[5],
                VSS[9]: landpattern.D[6],
                VSS[10]: landpattern.D[7],
                VDD2H[7]: landpattern.D[8],
                VSS[11]: landpattern.D[9],
                VSS[12]: landpattern.D[10],
                WCK_c_A[1]: landpattern.D[11],
                VDDQ[7]: landpattern.D[12],
                DQ_A[11]: landpattern.D[13],
                VSS[13]: landpattern.D[14],
                DQ_A[8]: landpattern.D[15],
                # Row E
                VSS[14]: landpattern.E[1],
                DQ_A[2]: landpattern.E[2],
                VSS[15]: landpattern.E[3],
                WCK_t_A[0]: landpattern.E[4],
                VDDQ[8]: landpattern.E[5],
                DQ_A[6]: landpattern.E[6],
                VDD2H[8]: landpattern.E[7],
                VSS[16]: landpattern.E[8],
                VDD2H[9]: landpattern.E[9],
                DQ_A[14]: landpattern.E[10],
                VDDQ[9]: landpattern.E[11],
                WCK_t_A[1]: landpattern.E[12],
                VSS[17]: landpattern.E[13],
                DQ_A[10]: landpattern.E[14],
                VSS[18]: landpattern.E[15],
                # Row F
                VDDQ[10]: landpattern.F[1],
                VSS[19]: landpattern.F[2],
                VDDQ[11]: landpattern.F[3],
                VDDQ[12]: landpattern.F[4],
                DQ_A[7]: landpattern.F[5],
                VDD2H[10]: landpattern.F[6],
                VDD2H[11]: landpattern.F[7],
                VSS[20]: landpattern.F[8],
                VDD2H[12]: landpattern.F[9],
                VDD2H[13]: landpattern.F[10],
                DQ_A[15]: landpattern.F[11],
                VDDQ[13]: landpattern.F[12],
                VDDQ[14]: landpattern.F[13],
                VSS[21]: landpattern.F[14],
                VDDQ[15]: landpattern.F[15],
                # Row G
                VDDQ[16]: landpattern.G[1],
                VDDQ[17]: landpattern.G[2],
                VSS[22]: landpattern.G[3],
                CA_A[0]: landpattern.G[4],
                VSS[23]: landpattern.G[5],
                CS_A[1]: landpattern.G[6],
                VSS[24]: landpattern.G[7],
                CA_A[2]: landpattern.G[8],
                VSS[25]: landpattern.G[9],
                CA_A[4]: landpattern.G[10],
                VSS[26]: landpattern.G[11],
                CA_A[6]: landpattern.G[12],
                VSS[27]: landpattern.G[13],
                VDDQ[18]: landpattern.G[14],
                VDDQ[19]: landpattern.G[15],
                # Row H
                RESET_N: landpattern.H[1],
                VDD2L[4]: landpattern.H[2],
                VSS[28]: landpattern.H[3],
                VSS[29]: landpattern.H[4],
                CA_A[1]: landpattern.H[5],
                VSS[30]: landpattern.H[6],
                CS_A[0]: landpattern.H[7],
                VSS[31]: landpattern.H[8],
                CK_t_A: landpattern.H[9],
                VSS[32]: landpattern.H[10],
                CA_A[3]: landpattern.H[11],
                VSS[33]: landpattern.H[12],
                CA_A[5]: landpattern.H[13],
                VDD2L[5]: landpattern.H[14],
                ZQ_A: landpattern.H[15],
                # Row J
                VSS[34]: landpattern.J[1],
                VDD2L[6]: landpattern.J[2],
                VSS[35]: landpattern.J[3],
                RFU[0]: landpattern.J[4],
                VDD2H[14]: landpattern.J[5],
                RFU[1]: landpattern.J[6],
                VSS[36]: landpattern.J[7],
                VSS[37]: landpattern.J[8],
                CK_c_A: landpattern.J[9],
                VSS[38]: landpattern.J[10],
                VDD2H[15]: landpattern.J[11],
                VSS[39]: landpattern.J[12],
                VSS[40]: landpattern.J[13],
                VDD2L[7]: landpattern.J[14],
                VSS[41]: landpattern.J[15],
                # Row K
                VDD2H[16]: landpattern.K[1],
                VDD2H[17]: landpattern.K[2],
                VDD2H[18]: landpattern.K[3],
                VDD2H[19]: landpattern.K[4],
                VDD2H[20]: landpattern.K[5],
                VDD2H[21]: landpattern.K[6],
                VSS[42]: landpattern.K[7],
                VSS[43]: landpattern.K[8],
                VSS[44]: landpattern.K[9],
                VDD2H[22]: landpattern.K[10],
                VDD2H[23]: landpattern.K[11],
                VDD2H[24]: landpattern.K[12],
                VDD2H[25]: landpattern.K[13],
                VDD2H[26]: landpattern.K[14],
                VDD2H[27]: landpattern.K[15],
                # Row L
                VSS[45]: landpattern.L[1],
                VSS[46]: landpattern.L[2],
                VSS[47]: landpattern.L[3],
                VSS[48]: landpattern.L[4],
                VSS[49]: landpattern.L[5],
                VDD2H[28]: landpattern.L[6],
                VDD2H[29]: landpattern.L[7],
                VDD2H[30]: landpattern.L[8],
                VDD2H[31]: landpattern.L[9],
                VDD2H[32]: landpattern.L[10],
                VSS[50]: landpattern.L[11],
                VSS[51]: landpattern.L[12],
                VSS[52]: landpattern.L[13],
                VSS[53]: landpattern.L[14],
                VSS[54]: landpattern.L[15],
                # Row M
                VDD2H[33]: landpattern.M[1],
                VDD2H[34]: landpattern.M[2],
                VDD2H[35]: landpattern.M[3],
                VDD2H[36]: landpattern.M[4],
                VDD2H[37]: landpattern.M[5],
                VDD2H[38]: landpattern.M[6],
                VSS[55]: landpattern.M[7],
                VSS[56]: landpattern.M[8],
                VSS[57]: landpattern.M[9],
                VDD2H[39]: landpattern.M[10],
                VDD2H[40]: landpattern.M[11],
                VDD2H[41]: landpattern.M[12],
                VDD2H[42]: landpattern.M[13],
                VDD2H[43]: landpattern.M[14],
                VDD2H[44]: landpattern.M[15],
                # Row N
                VSS[58]: landpattern.N[1],
                VDD2L[8]: landpattern.N[2],
                VSS[59]: landpattern.N[3],
                VSS[60]: landpattern.N[4],
                VDD2H[45]: landpattern.N[5],
                VSS[61]: landpattern.N[6],
                CK_c_B: landpattern.N[7],
                VSS[62]: landpattern.N[8],
                VSS[63]: landpattern.N[9],
                VSS[64]: landpattern.N[10],
                VDD2H[46]: landpattern.N[11],
                VSS[65]: landpattern.N[12],
                VSS[66]: landpattern.N[13],
                VDD2L[9]: landpattern.N[14],
                VSS[67]: landpattern.N[15],
                # Row P
                RFU[2]: landpattern.P[1],
                VDD2L[10]: landpattern.P[2],
                CA_B[5]: landpattern.P[3],
                VSS[68]: landpattern.P[4],
                CA_B[3]: landpattern.P[5],
                VSS[69]: landpattern.P[6],
                CK_t_B: landpattern.P[7],
                VSS[70]: landpattern.P[8],
                CS_B[0]: landpattern.P[9],
                VSS[71]: landpattern.P[10],
                CA_B[1]: landpattern.P[11],
                VSS[72]: landpattern.P[12],
                VSS[73]: landpattern.P[13],
                VDD2L[11]: landpattern.P[14],
                RFU[3]: landpattern.P[15],
                # Row R
                VDDQ[20]: landpattern.R[1],
                VDDQ[21]: landpattern.R[2],
                VSS[74]: landpattern.R[3],
                CA_B[6]: landpattern.R[4],
                VSS[75]: landpattern.R[5],
                CA_B[4]: landpattern.R[6],
                VSS[76]: landpattern.R[7],
                CA_B[2]: landpattern.R[8],
                VSS[77]: landpattern.R[9],
                CS_B[1]: landpattern.R[10],
                VSS[78]: landpattern.R[11],
                CA_B[0]: landpattern.R[12],
                VSS[79]: landpattern.R[13],
                VDDQ[22]: landpattern.R[14],
                VDDQ[23]: landpattern.R[15],
                # Row T
                VDDQ[24]: landpattern.T[1],
                VSS[80]: landpattern.T[2],
                VDDQ[25]: landpattern.T[3],
                VDDQ[26]: landpattern.T[4],
                DQ_B[15]: landpattern.T[5],
                VDD2H[47]: landpattern.T[6],
                VDD2H[48]: landpattern.T[7],
                VSS[81]: landpattern.T[8],
                VDD2H[49]: landpattern.T[9],
                VDD2H[50]: landpattern.T[10],
                DQ_B[7]: landpattern.T[11],
                VDDQ[27]: landpattern.T[12],
                VDDQ[28]: landpattern.T[13],
                VSS[82]: landpattern.T[14],
                VDDQ[29]: landpattern.T[15],
                # Row U
                VSS[83]: landpattern.U[1],
                DQ_B[10]: landpattern.U[2],
                VSS[84]: landpattern.U[3],
                WCK_t_B[1]: landpattern.U[4],
                VDDQ[30]: landpattern.U[5],
                DQ_B[14]: landpattern.U[6],
                VDD2H[51]: landpattern.U[7],
                VSS[85]: landpattern.U[8],
                VDD2H[52]: landpattern.U[9],
                DQ_B[6]: landpattern.U[10],
                VDDQ[31]: landpattern.U[11],
                WCK_t_B[0]: landpattern.U[12],
                VSS[86]: landpattern.U[13],
                DQ_B[2]: landpattern.U[14],
                VSS[87]: landpattern.U[15],
                # Row V
                DQ_B[8]: landpattern.V[1],
                VSS[88]: landpattern.V[2],
                DQ_B[11]: landpattern.V[3],
                VDDQ[32]: landpattern.V[4],
                WCK_c_B[1]: landpattern.V[5],
                VSS[89]: landpattern.V[6],
                VSS[90]: landpattern.V[7],
                VDD2H[53]: landpattern.V[8],
                VSS[91]: landpattern.V[9],
                VSS[92]: landpattern.V[10],
                WCK_c_B[0]: landpattern.V[11],
                VDDQ[33]: landpattern.V[12],
                DQ_B[3]: landpattern.V[13],
                VSS[93]: landpattern.V[14],
                DQ_B[0]: landpattern.V[15],
                # Row W
                VDD1[2]: landpattern.W[1],
                DQ_B[9]: landpattern.W[2],
                VDDQ[34]: landpattern.W[3],
                RDQS_c_B[1]: landpattern.W[4],
                VSS[94]: landpattern.W[5],
                DQ_B[13]: landpattern.W[6],
                VDD2H[54]: landpattern.W[7],
                VSS[95]: landpattern.W[8],
                VDD2H[55]: landpattern.W[9],
                DQ_B[5]: landpattern.W[10],
                VSS[96]: landpattern.W[11],
                RDQS_c_B[0]: landpattern.W[12],
                VDDQ[35]: landpattern.W[13],
                DQ_B[1]: landpattern.W[14],
                VDD1[3]: landpattern.W[15],
                # Row Y
                NC[6]: landpattern.Y[1],
                VDDQ[36]: landpattern.Y[2],
                RDQS_t_B[1]: landpattern.Y[3],
                VSS[97]: landpattern.Y[4],
                DQ_B[12]: landpattern.Y[5],
                VDD2L[12]: landpattern.Y[6],
                VDD2H[56]: landpattern.Y[7],
                VSS[98]: landpattern.Y[8],
                VDD2H[57]: landpattern.Y[9],
                VDD2L[13]: landpattern.Y[10],
                DQ_B[4]: landpattern.Y[11],
                VSS[99]: landpattern.Y[12],
                RDQS_t_B[0]: landpattern.Y[13],
                VDDQ[37]: landpattern.Y[14],
                NC[7]: landpattern.Y[15],
                # Row AA
                NC[8]: landpattern.AA[1],
                NC[9]: landpattern.AA[2],
                VDDQ[38]: landpattern.AA[3],
                DMI_B[1]: landpattern.AA[4],
                VSS[100]: landpattern.AA[5],
                VDD2L[14]: landpattern.AA[6],
                VDD2H[58]: landpattern.AA[7],
                VDD2H[59]: landpattern.AA[8],
                VDD2H[60]: landpattern.AA[9],
                VDD2L[15]: landpattern.AA[10],
                VSS[101]: landpattern.AA[11],
                DMI_B[0]: landpattern.AA[12],
                VDDQ[39]: landpattern.AA[13],
                NC[10]: landpattern.AA[14],
                NC[11]: landpattern.AA[15],
            }
        )
    ]


class LPDDR5MemoryCircuit(Circuit):
    """LPDDR5 Memory Module

    Wraps MT62F4G32D8DV_026_AIT_B component with direct LPDDR5 port.
    Uses LPDDR5 x32 DualRank configuration.

    Port mapping:
    - d[0][0]: Channel A, Lane 0 (DQ_A[0-7])
    - d[0][1]: Channel A, Lane 1 (DQ_A[8-15])
    - d[1][0]: Channel B, Lane 0 (DQ_B[0-7])
    - d[1][1]: Channel B, Lane 1 (DQ_B[8-15])
    """

    io = LPDDR5(LPDDR5Width.x32, LPDDR5Rank.DualRank)
    pwr = Power()
    zq = Port()

    def __init__(self):
        self.mem = MT62F4G32D8DV_026_AIT_B()

        topos = []

        # Reset signal
        topos.append(self.io.reset_n >> self.mem.RESET_N)

        # ZQ calibration (not in LPDDR5 bundle) - use + since not part of SI topology
        self.zq_net = self.zq + self.mem.ZQ_A

        # ======= Channel 0 (A) =======
        # CK
        topos.append(self.io.ck[0].p >> self.mem.CK_t_A)
        topos.append(self.io.ck[0].n >> self.mem.CK_c_A)

        # CS (2 ranks)
        topos.append(self.io.cs[0][0] >> self.mem.CS_A[0])
        topos.append(self.io.cs[0][1] >> self.mem.CS_A[1])

        # CA (7 bits)
        for i in range(7):
            topos.append(self.io.ca[0][i] >> self.mem.CA_A[i])

        # Data Lane 0: DQ_A[0-7], WCK0, RDQS0, DMI0
        for i in range(8):
            topos.append(self.io.d[0][0].dq[i] >> self.mem.DQ_A[i])
        topos.append(self.io.d[0][0].wck.p >> self.mem.WCK_t_A[0])
        topos.append(self.io.d[0][0].wck.n >> self.mem.WCK_c_A[0])
        topos.append(self.io.d[0][0].rdqs.p >> self.mem.RDQS_t_A[0])
        topos.append(self.io.d[0][0].rdqs.n >> self.mem.RDQS_c_A[0])
        topos.append(self.io.d[0][0].dmi >> self.mem.DMI_A[0])

        # Data Lane 1: DQ_A[8-15], WCK1, RDQS1, DMI1
        for i in range(8):
            topos.append(self.io.d[0][1].dq[i] >> self.mem.DQ_A[8 + i])
        topos.append(self.io.d[0][1].wck.p >> self.mem.WCK_t_A[1])
        topos.append(self.io.d[0][1].wck.n >> self.mem.WCK_c_A[1])
        topos.append(self.io.d[0][1].rdqs.p >> self.mem.RDQS_t_A[1])
        topos.append(self.io.d[0][1].rdqs.n >> self.mem.RDQS_c_A[1])
        topos.append(self.io.d[0][1].dmi >> self.mem.DMI_A[1])

        # ======= Channel 1 (B) =======
        # CK
        topos.append(self.io.ck[1].p >> self.mem.CK_t_B)
        topos.append(self.io.ck[1].n >> self.mem.CK_c_B)

        # CS (2 ranks)
        topos.append(self.io.cs[1][0] >> self.mem.CS_B[0])
        topos.append(self.io.cs[1][1] >> self.mem.CS_B[1])

        # CA (7 bits)
        for i in range(7):
            topos.append(self.io.ca[1][i] >> self.mem.CA_B[i])

        # Data Lane 0: DQ_B[0-7], WCK0, RDQS0, DMI0
        for i in range(8):
            topos.append(self.io.d[1][0].dq[i] >> self.mem.DQ_B[i])
        topos.append(self.io.d[1][0].wck.p >> self.mem.WCK_t_B[0])
        topos.append(self.io.d[1][0].wck.n >> self.mem.WCK_c_B[0])
        topos.append(self.io.d[1][0].rdqs.p >> self.mem.RDQS_t_B[0])
        topos.append(self.io.d[1][0].rdqs.n >> self.mem.RDQS_c_B[0])
        topos.append(self.io.d[1][0].dmi >> self.mem.DMI_B[0])

        # Data Lane 1: DQ_B[8-15], WCK1, RDQS1, DMI1
        for i in range(8):
            topos.append(self.io.d[1][1].dq[i] >> self.mem.DQ_B[8 + i])
        topos.append(self.io.d[1][1].wck.p >> self.mem.WCK_t_B[1])
        topos.append(self.io.d[1][1].wck.n >> self.mem.WCK_c_B[1])
        topos.append(self.io.d[1][1].rdqs.p >> self.mem.RDQS_t_B[1])
        topos.append(self.io.d[1][1].rdqs.n >> self.mem.RDQS_c_B[1])
        topos.append(self.io.d[1][1].dmi >> self.mem.DMI_B[1])

        self.topos = topos
