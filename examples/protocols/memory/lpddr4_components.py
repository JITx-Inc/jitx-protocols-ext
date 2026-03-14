"""LPDDR4 Example Components

LPDDR4 controller circuit.
Memory component and circuit live in K4FBE3D4HB_KHCL.py.
"""

from jitx import PadMapping, Provide
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.net import Port
from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol

from jitx_protocols_ext.protocols.memory.lpddr4 import LPDDR4, LPDDR4Rank, LPDDR4Width

from .K4FBE3D4HB_KHCL import K4FBE3D4HB_KHCL, LPDDR4MemoryCircuit  # noqa: F401


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
