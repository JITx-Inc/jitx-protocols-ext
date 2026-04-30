"""Xilinx Versal XC2VE3858 FPGA — full Python translation.

Translation of `components/xc2ve3858.stanza`:

- 46x46 SSVA2112 BGA landpattern (4 corners cut)
- 2112-pin :py:class:`XC2VE3858` component with full pad mapping
- :py:class:`XC2VE3858Circuit` wrapper exposing power rails, the full
  Versal protocol bundle library (GTYP / HDIO / PMC-MIO / LPD-MIO /
  MIPI-PHY / X5IO / GTR-USB3 / USB2 / JTAG / I3C-I2C), GTYP transceiver
  bias rails, configuration-bank single-ended signals, and 5
  ``Provide(LPDDR5)`` interfaces (one per DDR memory controller).
- ~735 ``Provide(GPIO)`` registrations covering every single-ended I/O
  pin on the protocol bundles.

Implementation choice for the LPDDR5 Provide: **option (a) — flat
per-packing mapping with fixed DQ-bit-to-pin assignment**. The recursive
per-DQ-bit Provide pattern from stanza ``make-lpddr5-supports`` (option
(b)) is documented in :py:meth:`XC2VE3858Circuit._build_lpddr5_mapping`'s
docstring as an upgrade path, but not implemented here.

Sources:

- Stanza component: customers/lockheed-martin/tssr-parts/xilinx/components/xc2ve3858.stanza
- Stanza landpattern: customers/lockheed-martin/tssr-parts/xilinx/landpatterns/ssva2112-bga.stanza
- Stanza bundles:    customers/lockheed-martin/tssr-parts/xilinx/bundles/versal.stanza
- AMD Versal datasheet: https://docs.amd.com/r/en-US/am013-versal-pkg-pinout
"""

from __future__ import annotations

from enum import Enum

from jitx import Net, PadMapping, Provide
from jitx.circuit import Circuit
from jitx.common import GPIO, Power
from jitx.component import Component
from jitx.net import DiffPair, Port
from jitx.toleranced import Toleranced
from jitx.transform import Transform
from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.grid_planner import CornerCutGridPlanner
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.protocols.serial import I2C, JTAG
from jitxlib.protocols.usb import USB2Connector
from jitxlib.symbols.box import BoxSymbol

from jitx_protocols_ext.protocols.memory.lpddr5 import LPDDR5, LPDDR5Rank, LPDDR5Width
from jitx_protocols_ext.protocols.xilinx_versal import (
    GTRUSB3,
    GTYPMMIQuad,
    GTYPQuad,
    HDIOBank,
    LPDMioBank,
    MIPIPhy,
    PMCMioBank,
    X5IOBank,
)


class SSVA2112BGALandpattern(BGA):
    """Xilinx Versal SSVA2112 — 46x46 BGA, 0.5 mm balls, 0.8 mm pitch.

    Corners are cut (1 ball per corner) per the package outline.
    """

    def __init__(self):
        super().__init__(
            num_rows=46,
            num_cols=46,
            ball_diameter=0.5,
            pitch=0.8,
        )
        self.grid_planner(CornerCutGridPlanner(corner_width=1))
        self.pad_config(SMDPadConfig())
        self.package_body(
            RectanglePackage(
                width=Toleranced.exact(37.5),
                length=Toleranced.exact(37.5),
                height=Toleranced.min_max(3.50, 3.90),
            )
        )
        self.density_level(DensityLevel.C)


class XC2VE3858(Component):
    """AMD/Xilinx Versal XC2VE3858 FPGA — 2112-ball SSVA2112 BGA.

    This Pass-A component declares the full pin map. Protocol bundle
    structure (gtyp/hdio/x5io/mipi) is deferred to Pass B; for the LPDDR5
    example the X5IO bank pins are exposed as flat ports, and the
    `XC2VE3858Circuit` wrapper provides the LPDDR5 interface via `Provide()`.
    """

    reference_prefix = "U"
    mpn = "XC2VE3858"
    manufacturer = "AMD/Xilinx"
    description = "Versal AI Edge Series VE3858 FPGA, 2112-ball SSVA2112 BGA"

    DONE_503 = Port()
    ERROR_OUT_503 = Port()
    GND = [Port() for _ in range(869)]
    GND_SMON = Port()
    GND_VCCINT_SENSE = Port()
    GND_VCC_AIE_SENSE = Port()
    GND_VCC_FPD_SENSE = Port()
    GND_VCC_SOC_SENSE = Port()
    GTYP_AVCCAUX_L = [Port() for _ in range(2)]
    GTYP_AVCCAUX_RN = [Port() for _ in range(2)]
    GTYP_AVCC_L = [Port() for _ in range(4)]
    GTYP_AVCC_RN = [Port() for _ in range(3)]
    GTYP_AVTTRCAL_L = Port()
    GTYP_AVTTRCAL_RN = Port()
    GTYP_AVTT_L = [Port() for _ in range(4)]
    GTYP_AVTT_RN = [Port() for _ in range(3)]
    GTYP_MMI_AVCCAUX_RS = [Port() for _ in range(2)]
    GTYP_MMI_AVCC_RS = [Port() for _ in range(2)]
    GTYP_MMI_AVTTRCAL_RS = Port()
    GTYP_MMI_AVTT_RS = [Port() for _ in range(2)]
    GTYP_MMI_REFCLKN0_105 = Port()
    GTYP_MMI_REFCLKN1_105 = Port()
    GTYP_MMI_REFCLKP0_105 = Port()
    GTYP_MMI_REFCLKP1_105 = Port()
    GTYP_MMI_RREF_RS = Port()
    GTYP_MMI_RXN0_105 = Port()
    GTYP_MMI_RXN1_105 = Port()
    GTYP_MMI_RXN2_105 = Port()
    GTYP_MMI_RXN3_105 = Port()
    GTYP_MMI_RXP0_105 = Port()
    GTYP_MMI_RXP1_105 = Port()
    GTYP_MMI_RXP2_105 = Port()
    GTYP_MMI_RXP3_105 = Port()
    GTYP_MMI_TXN0_105 = Port()
    GTYP_MMI_TXN1_105 = Port()
    GTYP_MMI_TXN2_105 = Port()
    GTYP_MMI_TXN3_105 = Port()
    GTYP_MMI_TXP0_105 = Port()
    GTYP_MMI_TXP1_105 = Port()
    GTYP_MMI_TXP2_105 = Port()
    GTYP_MMI_TXP3_105 = Port()
    GTYP_REFCLKN0_106 = Port()
    GTYP_REFCLKN0_107 = Port()
    GTYP_REFCLKN0_205 = Port()
    GTYP_REFCLKN0_206 = Port()
    GTYP_REFCLKN0_207 = Port()
    GTYP_REFCLKN1_106 = Port()
    GTYP_REFCLKN1_107 = Port()
    GTYP_REFCLKN1_205 = Port()
    GTYP_REFCLKN1_206 = Port()
    GTYP_REFCLKN1_207 = Port()
    GTYP_REFCLKP0_106 = Port()
    GTYP_REFCLKP0_107 = Port()
    GTYP_REFCLKP0_205 = Port()
    GTYP_REFCLKP0_206 = Port()
    GTYP_REFCLKP0_207 = Port()
    GTYP_REFCLKP1_106 = Port()
    GTYP_REFCLKP1_107 = Port()
    GTYP_REFCLKP1_205 = Port()
    GTYP_REFCLKP1_206 = Port()
    GTYP_REFCLKP1_207 = Port()
    GTYP_RREF_L = Port()
    GTYP_RREF_RN = Port()
    GTYP_RXN0_106 = Port()
    GTYP_RXN0_107 = Port()
    GTYP_RXN0_205 = Port()
    GTYP_RXN0_206 = Port()
    GTYP_RXN0_207 = Port()
    GTYP_RXN1_106 = Port()
    GTYP_RXN1_107 = Port()
    GTYP_RXN1_205 = Port()
    GTYP_RXN1_206 = Port()
    GTYP_RXN1_207 = Port()
    GTYP_RXN2_106 = Port()
    GTYP_RXN2_107 = Port()
    GTYP_RXN2_205 = Port()
    GTYP_RXN2_206 = Port()
    GTYP_RXN2_207 = Port()
    GTYP_RXN3_106 = Port()
    GTYP_RXN3_107 = Port()
    GTYP_RXN3_205 = Port()
    GTYP_RXN3_206 = Port()
    GTYP_RXN3_207 = Port()
    GTYP_RXP0_106 = Port()
    GTYP_RXP0_107 = Port()
    GTYP_RXP0_205 = Port()
    GTYP_RXP0_206 = Port()
    GTYP_RXP0_207 = Port()
    GTYP_RXP1_106 = Port()
    GTYP_RXP1_107 = Port()
    GTYP_RXP1_205 = Port()
    GTYP_RXP1_206 = Port()
    GTYP_RXP1_207 = Port()
    GTYP_RXP2_106 = Port()
    GTYP_RXP2_107 = Port()
    GTYP_RXP2_205 = Port()
    GTYP_RXP2_206 = Port()
    GTYP_RXP2_207 = Port()
    GTYP_RXP3_106 = Port()
    GTYP_RXP3_107 = Port()
    GTYP_RXP3_205 = Port()
    GTYP_RXP3_206 = Port()
    GTYP_RXP3_207 = Port()
    GTYP_TXN0_106 = Port()
    GTYP_TXN0_107 = Port()
    GTYP_TXN0_205 = Port()
    GTYP_TXN0_206 = Port()
    GTYP_TXN0_207 = Port()
    GTYP_TXN1_106 = Port()
    GTYP_TXN1_107 = Port()
    GTYP_TXN1_205 = Port()
    GTYP_TXN1_206 = Port()
    GTYP_TXN1_207 = Port()
    GTYP_TXN2_106 = Port()
    GTYP_TXN2_107 = Port()
    GTYP_TXN2_205 = Port()
    GTYP_TXN2_206 = Port()
    GTYP_TXN2_207 = Port()
    GTYP_TXN3_106 = Port()
    GTYP_TXN3_107 = Port()
    GTYP_TXN3_205 = Port()
    GTYP_TXN3_206 = Port()
    GTYP_TXN3_207 = Port()
    GTYP_TXP0_106 = Port()
    GTYP_TXP0_107 = Port()
    GTYP_TXP0_205 = Port()
    GTYP_TXP0_206 = Port()
    GTYP_TXP0_207 = Port()
    GTYP_TXP1_106 = Port()
    GTYP_TXP1_107 = Port()
    GTYP_TXP1_205 = Port()
    GTYP_TXP1_206 = Port()
    GTYP_TXP1_207 = Port()
    GTYP_TXP2_106 = Port()
    GTYP_TXP2_107 = Port()
    GTYP_TXP2_205 = Port()
    GTYP_TXP2_206 = Port()
    GTYP_TXP2_207 = Port()
    GTYP_TXP3_106 = Port()
    GTYP_TXP3_107 = Port()
    GTYP_TXP3_205 = Port()
    GTYP_TXP3_206 = Port()
    GTYP_TXP3_207 = Port()
    I3CI2C_SCL_503 = Port()
    I3CI2C_SDA_503 = Port()
    IO_L0N_400 = Port()
    IO_L0N_402 = Port()
    IO_L0N_H0O0P1_706 = Port()
    IO_L0N_H0O0P1_708 = Port()
    IO_L0N_H0O0P1_M0P1_700 = Port()
    IO_L0N_H0O0P1_M0P65_702 = Port()
    IO_L0N_H0O0P1_M1P129_704 = Port()
    IO_L0N_H0O0P1_M2P1_710 = Port()
    IO_L0N_H0O0P1_M2P65_712 = Port()
    IO_L0N_H0O0P1_M3P129_714 = Port()
    IO_L0P_400 = Port()
    IO_L0P_402 = Port()
    IO_L0P_H0O0P0_706 = Port()
    IO_L0P_H0O0P0_708 = Port()
    IO_L0P_H0O0P0_M0P0_700 = Port()
    IO_L0P_H0O0P0_M0P64_702 = Port()
    IO_L0P_H0O0P0_M1P128_704 = Port()
    IO_L0P_H0O0P0_M2P0_710 = Port()
    IO_L0P_H0O0P0_M2P64_712 = Port()
    IO_L0P_H0O0P0_M3P128_714 = Port()
    IO_L10N_400 = Port()
    IO_L10N_402 = Port()
    IO_L10N_H0O2P5_706 = Port()
    IO_L10N_H0O2P5_708 = Port()
    IO_L10N_H0O2P5_M0P21_700 = Port()
    IO_L10N_H0O2P5_M0P85_702 = Port()
    IO_L10N_H0O2P5_M1P149_704 = Port()
    IO_L10N_H0O2P5_M2P21_710 = Port()
    IO_L10N_H0O2P5_M2P85_712 = Port()
    IO_L10N_H0O2P5_M3P149_714 = Port()
    IO_L10P_400 = Port()
    IO_L10P_402 = Port()
    IO_L10P_H0O2P4_706 = Port()
    IO_L10P_H0O2P4_708 = Port()
    IO_L10P_H0O2P4_M0P20_700 = Port()
    IO_L10P_H0O2P4_M0P84_702 = Port()
    IO_L10P_H0O2P4_M1P148_704 = Port()
    IO_L10P_H0O2P4_M2P20_710 = Port()
    IO_L10P_H0O2P4_M2P84_712 = Port()
    IO_L10P_H0O2P4_M3P148_714 = Port()
    IO_L11N_H0O2P7_706 = Port()
    IO_L11N_H0O2P7_708 = Port()
    IO_L11N_H0O2P7_M0P23_700 = Port()
    IO_L11N_H0O2P7_M0P87_702 = Port()
    IO_L11N_H0O2P7_M1P151_704 = Port()
    IO_L11N_H0O2P7_M2P23_710 = Port()
    IO_L11N_H0O2P7_M2P87_712 = Port()
    IO_L11N_H0O2P7_M3P151_714 = Port()
    IO_L11P_H0O2P6_706 = Port()
    IO_L11P_H0O2P6_708 = Port()
    IO_L11P_H0O2P6_M0P22_700 = Port()
    IO_L11P_H0O2P6_M0P86_702 = Port()
    IO_L11P_H0O2P6_M1P150_704 = Port()
    IO_L11P_H0O2P6_M2P22_710 = Port()
    IO_L11P_H0O2P6_M2P86_712 = Port()
    IO_L11P_H0O2P6_M3P150_714 = Port()
    IO_L12N_H0O3P1_706 = Port()
    IO_L12N_H0O3P1_708 = Port()
    IO_L12N_H0O3P1_M0P25_700 = Port()
    IO_L12N_H0O3P1_M0P89_702 = Port()
    IO_L12N_H0O3P1_M1P153_704 = Port()
    IO_L12N_H0O3P1_M2P25_710 = Port()
    IO_L12N_H0O3P1_M2P89_712 = Port()
    IO_L12N_H0O3P1_M3P153_714 = Port()
    IO_L12P_H0O3P0_706 = Port()
    IO_L12P_H0O3P0_708 = Port()
    IO_L12P_H0O3P0_M0P24_700 = Port()
    IO_L12P_H0O3P0_M0P88_702 = Port()
    IO_L12P_H0O3P0_M1P152_704 = Port()
    IO_L12P_H0O3P0_M2P24_710 = Port()
    IO_L12P_H0O3P0_M2P88_712 = Port()
    IO_L12P_H0O3P0_M3P152_714 = Port()
    IO_L13N_XCC_H0O3P3_706 = Port()
    IO_L13N_XCC_H0O3P3_708 = Port()
    IO_L13N_XCC_H0O3P3_M0P27_700 = Port()
    IO_L13N_XCC_H0O3P3_M0P91_702 = Port()
    IO_L13N_XCC_H0O3P3_M1P155_704 = Port()
    IO_L13N_XCC_H0O3P3_M2P27_710 = Port()
    IO_L13N_XCC_H0O3P3_M2P91_712 = Port()
    IO_L13N_XCC_H0O3P3_M3P155_714 = Port()
    IO_L13P_XCC_H0O3P2_706 = Port()
    IO_L13P_XCC_H0O3P2_708 = Port()
    IO_L13P_XCC_H0O3P2_M0P26_700 = Port()
    IO_L13P_XCC_H0O3P2_M0P90_702 = Port()
    IO_L13P_XCC_H0O3P2_M1P154_704 = Port()
    IO_L13P_XCC_H0O3P2_M2P26_710 = Port()
    IO_L13P_XCC_H0O3P2_M2P90_712 = Port()
    IO_L13P_XCC_H0O3P2_M3P154_714 = Port()
    IO_L14N_H0O3P5_706 = Port()
    IO_L14N_H0O3P5_708 = Port()
    IO_L14N_H0O3P5_M0P29_700 = Port()
    IO_L14N_H0O3P5_M0P93_702 = Port()
    IO_L14N_H0O3P5_M1P157_704 = Port()
    IO_L14N_H0O3P5_M2P29_710 = Port()
    IO_L14N_H0O3P5_M2P93_712 = Port()
    IO_L14N_H0O3P5_M3P157_714 = Port()
    IO_L14P_H0O3P4_706 = Port()
    IO_L14P_H0O3P4_708 = Port()
    IO_L14P_H0O3P4_M0P28_700 = Port()
    IO_L14P_H0O3P4_M0P92_702 = Port()
    IO_L14P_H0O3P4_M1P156_704 = Port()
    IO_L14P_H0O3P4_M2P28_710 = Port()
    IO_L14P_H0O3P4_M2P92_712 = Port()
    IO_L14P_H0O3P4_M3P156_714 = Port()
    IO_L15N_H0O3P7_706 = Port()
    IO_L15N_H0O3P7_708 = Port()
    IO_L15N_H0O3P7_M0P31_700 = Port()
    IO_L15N_H0O3P7_M0P95_702 = Port()
    IO_L15N_H0O3P7_M1P159_704 = Port()
    IO_L15N_H0O3P7_M2P31_710 = Port()
    IO_L15N_H0O3P7_M2P95_712 = Port()
    IO_L15N_H0O3P7_M3P159_714 = Port()
    IO_L15P_H0O3P6_706 = Port()
    IO_L15P_H0O3P6_708 = Port()
    IO_L15P_H0O3P6_M0P30_700 = Port()
    IO_L15P_H0O3P6_M0P94_702 = Port()
    IO_L15P_H0O3P6_M1P158_704 = Port()
    IO_L15P_H0O3P6_M2P30_710 = Port()
    IO_L15P_H0O3P6_M2P94_712 = Port()
    IO_L15P_H0O3P6_M3P158_714 = Port()
    IO_L16N_H1O0P1_707 = Port()
    IO_L16N_H1O0P1_709 = Port()
    IO_L16N_H1O0P1_M0P33_701 = Port()
    IO_L16N_H1O0P1_M1P161_705 = Port()
    IO_L16N_H1O0P1_M1P97_703 = Port()
    IO_L16N_H1O0P1_M2P33_711 = Port()
    IO_L16N_H1O0P1_M3P161_715 = Port()
    IO_L16N_H1O0P1_M3P97_713 = Port()
    IO_L16P_H1O0P0_707 = Port()
    IO_L16P_H1O0P0_709 = Port()
    IO_L16P_H1O0P0_M0P32_701 = Port()
    IO_L16P_H1O0P0_M1P160_705 = Port()
    IO_L16P_H1O0P0_M1P96_703 = Port()
    IO_L16P_H1O0P0_M2P32_711 = Port()
    IO_L16P_H1O0P0_M3P160_715 = Port()
    IO_L16P_H1O0P0_M3P96_713 = Port()
    IO_L17N_XCC_H1O0P3_707 = Port()
    IO_L17N_XCC_H1O0P3_709 = Port()
    IO_L17N_XCC_H1O0P3_M0P35_701 = Port()
    IO_L17N_XCC_H1O0P3_M1P163_705 = Port()
    IO_L17N_XCC_H1O0P3_M1P99_703 = Port()
    IO_L17N_XCC_H1O0P3_M2P35_711 = Port()
    IO_L17N_XCC_H1O0P3_M3P163_715 = Port()
    IO_L17N_XCC_H1O0P3_M3P99_713 = Port()
    IO_L17P_XCC_H1O0P2_707 = Port()
    IO_L17P_XCC_H1O0P2_709 = Port()
    IO_L17P_XCC_H1O0P2_M0P34_701 = Port()
    IO_L17P_XCC_H1O0P2_M1P162_705 = Port()
    IO_L17P_XCC_H1O0P2_M1P98_703 = Port()
    IO_L17P_XCC_H1O0P2_M2P34_711 = Port()
    IO_L17P_XCC_H1O0P2_M3P162_715 = Port()
    IO_L17P_XCC_H1O0P2_M3P98_713 = Port()
    IO_L18N_H1O0P5_707 = Port()
    IO_L18N_H1O0P5_709 = Port()
    IO_L18N_H1O0P5_M0P37_701 = Port()
    IO_L18N_H1O0P5_M1P101_703 = Port()
    IO_L18N_H1O0P5_M1P165_705 = Port()
    IO_L18N_H1O0P5_M2P37_711 = Port()
    IO_L18N_H1O0P5_M3P101_713 = Port()
    IO_L18N_H1O0P5_M3P165_715 = Port()
    IO_L18P_H1O0P4_707 = Port()
    IO_L18P_H1O0P4_709 = Port()
    IO_L18P_H1O0P4_M0P36_701 = Port()
    IO_L18P_H1O0P4_M1P100_703 = Port()
    IO_L18P_H1O0P4_M1P164_705 = Port()
    IO_L18P_H1O0P4_M2P36_711 = Port()
    IO_L18P_H1O0P4_M3P100_713 = Port()
    IO_L18P_H1O0P4_M3P164_715 = Port()
    IO_L19N_GC_H1O0P7_707 = Port()
    IO_L19N_GC_H1O0P7_709 = Port()
    IO_L19N_GC_H1O0P7_M0P39_701 = Port()
    IO_L19N_GC_H1O0P7_M1P103_703 = Port()
    IO_L19N_GC_H1O0P7_M1P167_705 = Port()
    IO_L19N_GC_H1O0P7_M2P39_711 = Port()
    IO_L19N_GC_H1O0P7_M3P103_713 = Port()
    IO_L19N_GC_H1O0P7_M3P167_715 = Port()
    IO_L19P_GC_H1O0P6_707 = Port()
    IO_L19P_GC_H1O0P6_709 = Port()
    IO_L19P_GC_H1O0P6_M0P38_701 = Port()
    IO_L19P_GC_H1O0P6_M1P102_703 = Port()
    IO_L19P_GC_H1O0P6_M1P166_705 = Port()
    IO_L19P_GC_H1O0P6_M2P38_711 = Port()
    IO_L19P_GC_H1O0P6_M3P102_713 = Port()
    IO_L19P_GC_H1O0P6_M3P166_715 = Port()
    IO_L1N_400 = Port()
    IO_L1N_402 = Port()
    IO_L1N_XCC_H0O0P3_706 = Port()
    IO_L1N_XCC_H0O0P3_708 = Port()
    IO_L1N_XCC_H0O0P3_M0P3_700 = Port()
    IO_L1N_XCC_H0O0P3_M0P67_702 = Port()
    IO_L1N_XCC_H0O0P3_M1P131_704 = Port()
    IO_L1N_XCC_H0O0P3_M2P3_710 = Port()
    IO_L1N_XCC_H0O0P3_M2P67_712 = Port()
    IO_L1N_XCC_H0O0P3_M3P131_714 = Port()
    IO_L1P_400 = Port()
    IO_L1P_402 = Port()
    IO_L1P_XCC_H0O0P2_706 = Port()
    IO_L1P_XCC_H0O0P2_708 = Port()
    IO_L1P_XCC_H0O0P2_M0P2_700 = Port()
    IO_L1P_XCC_H0O0P2_M0P66_702 = Port()
    IO_L1P_XCC_H0O0P2_M1P130_704 = Port()
    IO_L1P_XCC_H0O0P2_M2P2_710 = Port()
    IO_L1P_XCC_H0O0P2_M2P66_712 = Port()
    IO_L1P_XCC_H0O0P2_M3P130_714 = Port()
    IO_L20N_H1O1P1_707 = Port()
    IO_L20N_H1O1P1_709 = Port()
    IO_L20N_H1O1P1_M0P41_701 = Port()
    IO_L20N_H1O1P1_M1P105_703 = Port()
    IO_L20N_H1O1P1_M1P169_705 = Port()
    IO_L20N_H1O1P1_M2P41_711 = Port()
    IO_L20N_H1O1P1_M3P105_713 = Port()
    IO_L20N_H1O1P1_M3P169_715 = Port()
    IO_L20P_H1O1P0_707 = Port()
    IO_L20P_H1O1P0_709 = Port()
    IO_L20P_H1O1P0_M0P40_701 = Port()
    IO_L20P_H1O1P0_M1P104_703 = Port()
    IO_L20P_H1O1P0_M1P168_705 = Port()
    IO_L20P_H1O1P0_M2P40_711 = Port()
    IO_L20P_H1O1P0_M3P104_713 = Port()
    IO_L20P_H1O1P0_M3P168_715 = Port()
    IO_L21N_XCC_H1O1P3_707 = Port()
    IO_L21N_XCC_H1O1P3_709 = Port()
    IO_L21N_XCC_H1O1P3_M0P43_701 = Port()
    IO_L21N_XCC_H1O1P3_M1P107_703 = Port()
    IO_L21N_XCC_H1O1P3_M1P171_705 = Port()
    IO_L21N_XCC_H1O1P3_M2P43_711 = Port()
    IO_L21N_XCC_H1O1P3_M3P107_713 = Port()
    IO_L21N_XCC_H1O1P3_M3P171_715 = Port()
    IO_L21P_XCC_H1O1P2_707 = Port()
    IO_L21P_XCC_H1O1P2_709 = Port()
    IO_L21P_XCC_H1O1P2_M0P42_701 = Port()
    IO_L21P_XCC_H1O1P2_M1P106_703 = Port()
    IO_L21P_XCC_H1O1P2_M1P170_705 = Port()
    IO_L21P_XCC_H1O1P2_M2P42_711 = Port()
    IO_L21P_XCC_H1O1P2_M3P106_713 = Port()
    IO_L21P_XCC_H1O1P2_M3P170_715 = Port()
    IO_L22N_H1O1P5_707 = Port()
    IO_L22N_H1O1P5_709 = Port()
    IO_L22N_H1O1P5_M0P45_701 = Port()
    IO_L22N_H1O1P5_M1P109_703 = Port()
    IO_L22N_H1O1P5_M1P173_705 = Port()
    IO_L22N_H1O1P5_M2P45_711 = Port()
    IO_L22N_H1O1P5_M3P109_713 = Port()
    IO_L22N_H1O1P5_M3P173_715 = Port()
    IO_L22P_H1O1P4_707 = Port()
    IO_L22P_H1O1P4_709 = Port()
    IO_L22P_H1O1P4_M0P44_701 = Port()
    IO_L22P_H1O1P4_M1P108_703 = Port()
    IO_L22P_H1O1P4_M1P172_705 = Port()
    IO_L22P_H1O1P4_M2P44_711 = Port()
    IO_L22P_H1O1P4_M3P108_713 = Port()
    IO_L22P_H1O1P4_M3P172_715 = Port()
    IO_L23N_H1O1P7_707 = Port()
    IO_L23N_H1O1P7_709 = Port()
    IO_L23N_H1O1P7_M0P47_701 = Port()
    IO_L23N_H1O1P7_M1P111_703 = Port()
    IO_L23N_H1O1P7_M1P175_705 = Port()
    IO_L23N_H1O1P7_M2P47_711 = Port()
    IO_L23N_H1O1P7_M3P111_713 = Port()
    IO_L23N_H1O1P7_M3P175_715 = Port()
    IO_L23P_H1O1P6_707 = Port()
    IO_L23P_H1O1P6_709 = Port()
    IO_L23P_H1O1P6_M0P46_701 = Port()
    IO_L23P_H1O1P6_M1P110_703 = Port()
    IO_L23P_H1O1P6_M1P174_705 = Port()
    IO_L23P_H1O1P6_M2P46_711 = Port()
    IO_L23P_H1O1P6_M3P110_713 = Port()
    IO_L23P_H1O1P6_M3P174_715 = Port()
    IO_L24N_H1O2P1_707 = Port()
    IO_L24N_H1O2P1_709 = Port()
    IO_L24N_H1O2P1_M0P49_701 = Port()
    IO_L24N_H1O2P1_M1P113_703 = Port()
    IO_L24N_H1O2P1_M1P177_705 = Port()
    IO_L24N_H1O2P1_M2P49_711 = Port()
    IO_L24N_H1O2P1_M3P113_713 = Port()
    IO_L24N_H1O2P1_M3P177_715 = Port()
    IO_L24P_H1O2P0_707 = Port()
    IO_L24P_H1O2P0_709 = Port()
    IO_L24P_H1O2P0_M0P48_701 = Port()
    IO_L24P_H1O2P0_M1P112_703 = Port()
    IO_L24P_H1O2P0_M1P176_705 = Port()
    IO_L24P_H1O2P0_M2P48_711 = Port()
    IO_L24P_H1O2P0_M3P112_713 = Port()
    IO_L24P_H1O2P0_M3P176_715 = Port()
    IO_L25N_XCC_H1O2P3_707 = Port()
    IO_L25N_XCC_H1O2P3_709 = Port()
    IO_L25N_XCC_H1O2P3_M0P51_701 = Port()
    IO_L25N_XCC_H1O2P3_M1P115_703 = Port()
    IO_L25N_XCC_H1O2P3_M1P179_705 = Port()
    IO_L25N_XCC_H1O2P3_M2P51_711 = Port()
    IO_L25N_XCC_H1O2P3_M3P115_713 = Port()
    IO_L25N_XCC_H1O2P3_M3P179_715 = Port()
    IO_L25P_XCC_H1O2P2_707 = Port()
    IO_L25P_XCC_H1O2P2_709 = Port()
    IO_L25P_XCC_H1O2P2_M0P50_701 = Port()
    IO_L25P_XCC_H1O2P2_M1P114_703 = Port()
    IO_L25P_XCC_H1O2P2_M1P178_705 = Port()
    IO_L25P_XCC_H1O2P2_M2P50_711 = Port()
    IO_L25P_XCC_H1O2P2_M3P114_713 = Port()
    IO_L25P_XCC_H1O2P2_M3P178_715 = Port()
    IO_L26N_H1O2P5_707 = Port()
    IO_L26N_H1O2P5_709 = Port()
    IO_L26N_H1O2P5_M0P53_701 = Port()
    IO_L26N_H1O2P5_M1P117_703 = Port()
    IO_L26N_H1O2P5_M1P181_705 = Port()
    IO_L26N_H1O2P5_M2P53_711 = Port()
    IO_L26N_H1O2P5_M3P117_713 = Port()
    IO_L26N_H1O2P5_M3P181_715 = Port()
    IO_L26P_H1O2P4_707 = Port()
    IO_L26P_H1O2P4_709 = Port()
    IO_L26P_H1O2P4_M0P52_701 = Port()
    IO_L26P_H1O2P4_M1P116_703 = Port()
    IO_L26P_H1O2P4_M1P180_705 = Port()
    IO_L26P_H1O2P4_M2P52_711 = Port()
    IO_L26P_H1O2P4_M3P116_713 = Port()
    IO_L26P_H1O2P4_M3P180_715 = Port()
    IO_L27N_H1O2P7_707 = Port()
    IO_L27N_H1O2P7_709 = Port()
    IO_L27N_H1O2P7_M0P55_701 = Port()
    IO_L27N_H1O2P7_M1P119_703 = Port()
    IO_L27N_H1O2P7_M1P183_705 = Port()
    IO_L27N_H1O2P7_M2P55_711 = Port()
    IO_L27N_H1O2P7_M3P119_713 = Port()
    IO_L27N_H1O2P7_M3P183_715 = Port()
    IO_L27P_H1O2P6_707 = Port()
    IO_L27P_H1O2P6_709 = Port()
    IO_L27P_H1O2P6_M0P54_701 = Port()
    IO_L27P_H1O2P6_M1P118_703 = Port()
    IO_L27P_H1O2P6_M1P182_705 = Port()
    IO_L27P_H1O2P6_M2P54_711 = Port()
    IO_L27P_H1O2P6_M3P118_713 = Port()
    IO_L27P_H1O2P6_M3P182_715 = Port()
    IO_L28N_H1O3P1_707 = Port()
    IO_L28N_H1O3P1_709 = Port()
    IO_L28N_H1O3P1_M0P57_701 = Port()
    IO_L28N_H1O3P1_M1P121_703 = Port()
    IO_L28N_H1O3P1_M1P185_705 = Port()
    IO_L28N_H1O3P1_M2P57_711 = Port()
    IO_L28N_H1O3P1_M3P121_713 = Port()
    IO_L28N_H1O3P1_M3P185_715 = Port()
    IO_L28P_H1O3P0_707 = Port()
    IO_L28P_H1O3P0_709 = Port()
    IO_L28P_H1O3P0_M0P56_701 = Port()
    IO_L28P_H1O3P0_M1P120_703 = Port()
    IO_L28P_H1O3P0_M1P184_705 = Port()
    IO_L28P_H1O3P0_M2P56_711 = Port()
    IO_L28P_H1O3P0_M3P120_713 = Port()
    IO_L28P_H1O3P0_M3P184_715 = Port()
    IO_L29N_XCC_H1O3P3_707 = Port()
    IO_L29N_XCC_H1O3P3_709 = Port()
    IO_L29N_XCC_H1O3P3_M0P59_701 = Port()
    IO_L29N_XCC_H1O3P3_M1P123_703 = Port()
    IO_L29N_XCC_H1O3P3_M1P187_705 = Port()
    IO_L29N_XCC_H1O3P3_M2P59_711 = Port()
    IO_L29N_XCC_H1O3P3_M3P123_713 = Port()
    IO_L29N_XCC_H1O3P3_M3P187_715 = Port()
    IO_L29P_XCC_H1O3P2_707 = Port()
    IO_L29P_XCC_H1O3P2_709 = Port()
    IO_L29P_XCC_H1O3P2_M0P58_701 = Port()
    IO_L29P_XCC_H1O3P2_M1P122_703 = Port()
    IO_L29P_XCC_H1O3P2_M1P186_705 = Port()
    IO_L29P_XCC_H1O3P2_M2P58_711 = Port()
    IO_L29P_XCC_H1O3P2_M3P122_713 = Port()
    IO_L29P_XCC_H1O3P2_M3P186_715 = Port()
    IO_L2N_400 = Port()
    IO_L2N_402 = Port()
    IO_L2N_H0O0P5_706 = Port()
    IO_L2N_H0O0P5_708 = Port()
    IO_L2N_H0O0P5_M0P5_700 = Port()
    IO_L2N_H0O0P5_M0P69_702 = Port()
    IO_L2N_H0O0P5_M1P133_704 = Port()
    IO_L2N_H0O0P5_M2P5_710 = Port()
    IO_L2N_H0O0P5_M2P69_712 = Port()
    IO_L2N_H0O0P5_M3P133_714 = Port()
    IO_L2P_400 = Port()
    IO_L2P_402 = Port()
    IO_L2P_H0O0P4_706 = Port()
    IO_L2P_H0O0P4_708 = Port()
    IO_L2P_H0O0P4_M0P4_700 = Port()
    IO_L2P_H0O0P4_M0P68_702 = Port()
    IO_L2P_H0O0P4_M1P132_704 = Port()
    IO_L2P_H0O0P4_M2P4_710 = Port()
    IO_L2P_H0O0P4_M2P68_712 = Port()
    IO_L2P_H0O0P4_M3P132_714 = Port()
    IO_L30N_H1O3P5_707 = Port()
    IO_L30N_H1O3P5_709 = Port()
    IO_L30N_H1O3P5_M0P61_701 = Port()
    IO_L30N_H1O3P5_M1P125_703 = Port()
    IO_L30N_H1O3P5_M1P189_705 = Port()
    IO_L30N_H1O3P5_M2P61_711 = Port()
    IO_L30N_H1O3P5_M3P125_713 = Port()
    IO_L30N_H1O3P5_M3P189_715 = Port()
    IO_L30P_H1O3P4_707 = Port()
    IO_L30P_H1O3P4_709 = Port()
    IO_L30P_H1O3P4_M0P60_701 = Port()
    IO_L30P_H1O3P4_M1P124_703 = Port()
    IO_L30P_H1O3P4_M1P188_705 = Port()
    IO_L30P_H1O3P4_M2P60_711 = Port()
    IO_L30P_H1O3P4_M3P124_713 = Port()
    IO_L30P_H1O3P4_M3P188_715 = Port()
    IO_L31N_H1O3P7_707 = Port()
    IO_L31N_H1O3P7_709 = Port()
    IO_L31N_H1O3P7_M0P63_701 = Port()
    IO_L31N_H1O3P7_M1P127_703 = Port()
    IO_L31N_H1O3P7_M1P191_705 = Port()
    IO_L31N_H1O3P7_M2P63_711 = Port()
    IO_L31N_H1O3P7_M3P127_713 = Port()
    IO_L31N_H1O3P7_M3P191_715 = Port()
    IO_L31P_H1O3P6_707 = Port()
    IO_L31P_H1O3P6_709 = Port()
    IO_L31P_H1O3P6_M0P62_701 = Port()
    IO_L31P_H1O3P6_M1P126_703 = Port()
    IO_L31P_H1O3P6_M1P190_705 = Port()
    IO_L31P_H1O3P6_M2P62_711 = Port()
    IO_L31P_H1O3P6_M3P126_713 = Port()
    IO_L31P_H1O3P6_M3P190_715 = Port()
    IO_L3N_400 = Port()
    IO_L3N_402 = Port()
    IO_L3N_GC_H0O0P7_706 = Port()
    IO_L3N_GC_H0O0P7_708 = Port()
    IO_L3N_GC_H0O0P7_M0P71_702 = Port()
    IO_L3N_GC_H0O0P7_M0P7_700 = Port()
    IO_L3N_GC_H0O0P7_M1P135_704 = Port()
    IO_L3N_GC_H0O0P7_M2P71_712 = Port()
    IO_L3N_GC_H0O0P7_M2P7_710 = Port()
    IO_L3N_GC_H0O0P7_M3P135_714 = Port()
    IO_L3P_400 = Port()
    IO_L3P_402 = Port()
    IO_L3P_GC_H0O0P6_706 = Port()
    IO_L3P_GC_H0O0P6_708 = Port()
    IO_L3P_GC_H0O0P6_M0P6_700 = Port()
    IO_L3P_GC_H0O0P6_M0P70_702 = Port()
    IO_L3P_GC_H0O0P6_M1P134_704 = Port()
    IO_L3P_GC_H0O0P6_M2P6_710 = Port()
    IO_L3P_GC_H0O0P6_M2P70_712 = Port()
    IO_L3P_GC_H0O0P6_M3P134_714 = Port()
    IO_L4N_400 = Port()
    IO_L4N_402 = Port()
    IO_L4N_H0O1P1_706 = Port()
    IO_L4N_H0O1P1_708 = Port()
    IO_L4N_H0O1P1_M0P73_702 = Port()
    IO_L4N_H0O1P1_M0P9_700 = Port()
    IO_L4N_H0O1P1_M1P137_704 = Port()
    IO_L4N_H0O1P1_M2P73_712 = Port()
    IO_L4N_H0O1P1_M2P9_710 = Port()
    IO_L4N_H0O1P1_M3P137_714 = Port()
    IO_L4P_400 = Port()
    IO_L4P_402 = Port()
    IO_L4P_H0O1P0_706 = Port()
    IO_L4P_H0O1P0_708 = Port()
    IO_L4P_H0O1P0_M0P72_702 = Port()
    IO_L4P_H0O1P0_M0P8_700 = Port()
    IO_L4P_H0O1P0_M1P136_704 = Port()
    IO_L4P_H0O1P0_M2P72_712 = Port()
    IO_L4P_H0O1P0_M2P8_710 = Port()
    IO_L4P_H0O1P0_M3P136_714 = Port()
    IO_L5N_HDGC_400 = Port()
    IO_L5N_HDGC_402 = Port()
    IO_L5N_XCC_H0O1P3_706 = Port()
    IO_L5N_XCC_H0O1P3_708 = Port()
    IO_L5N_XCC_H0O1P3_M0P11_700 = Port()
    IO_L5N_XCC_H0O1P3_M0P75_702 = Port()
    IO_L5N_XCC_H0O1P3_M1P139_704 = Port()
    IO_L5N_XCC_H0O1P3_M2P11_710 = Port()
    IO_L5N_XCC_H0O1P3_M2P75_712 = Port()
    IO_L5N_XCC_H0O1P3_M3P139_714 = Port()
    IO_L5P_HDGC_400 = Port()
    IO_L5P_HDGC_402 = Port()
    IO_L5P_XCC_H0O1P2_706 = Port()
    IO_L5P_XCC_H0O1P2_708 = Port()
    IO_L5P_XCC_H0O1P2_M0P10_700 = Port()
    IO_L5P_XCC_H0O1P2_M0P74_702 = Port()
    IO_L5P_XCC_H0O1P2_M1P138_704 = Port()
    IO_L5P_XCC_H0O1P2_M2P10_710 = Port()
    IO_L5P_XCC_H0O1P2_M2P74_712 = Port()
    IO_L5P_XCC_H0O1P2_M3P138_714 = Port()
    IO_L6N_H0O1P5_706 = Port()
    IO_L6N_H0O1P5_708 = Port()
    IO_L6N_H0O1P5_M0P13_700 = Port()
    IO_L6N_H0O1P5_M0P77_702 = Port()
    IO_L6N_H0O1P5_M1P141_704 = Port()
    IO_L6N_H0O1P5_M2P13_710 = Port()
    IO_L6N_H0O1P5_M2P77_712 = Port()
    IO_L6N_H0O1P5_M3P141_714 = Port()
    IO_L6N_HDGC_400 = Port()
    IO_L6N_HDGC_402 = Port()
    IO_L6P_H0O1P4_706 = Port()
    IO_L6P_H0O1P4_708 = Port()
    IO_L6P_H0O1P4_M0P12_700 = Port()
    IO_L6P_H0O1P4_M0P76_702 = Port()
    IO_L6P_H0O1P4_M1P140_704 = Port()
    IO_L6P_H0O1P4_M2P12_710 = Port()
    IO_L6P_H0O1P4_M2P76_712 = Port()
    IO_L6P_H0O1P4_M3P140_714 = Port()
    IO_L6P_HDGC_400 = Port()
    IO_L6P_HDGC_402 = Port()
    IO_L7N_400 = Port()
    IO_L7N_402 = Port()
    IO_L7N_H0O1P7_706 = Port()
    IO_L7N_H0O1P7_708 = Port()
    IO_L7N_H0O1P7_M0P15_700 = Port()
    IO_L7N_H0O1P7_M0P79_702 = Port()
    IO_L7N_H0O1P7_M1P143_704 = Port()
    IO_L7N_H0O1P7_M2P15_710 = Port()
    IO_L7N_H0O1P7_M2P79_712 = Port()
    IO_L7N_H0O1P7_M3P143_714 = Port()
    IO_L7P_400 = Port()
    IO_L7P_402 = Port()
    IO_L7P_H0O1P6_706 = Port()
    IO_L7P_H0O1P6_708 = Port()
    IO_L7P_H0O1P6_M0P14_700 = Port()
    IO_L7P_H0O1P6_M0P78_702 = Port()
    IO_L7P_H0O1P6_M1P142_704 = Port()
    IO_L7P_H0O1P6_M2P14_710 = Port()
    IO_L7P_H0O1P6_M2P78_712 = Port()
    IO_L7P_H0O1P6_M3P142_714 = Port()
    IO_L8N_400 = Port()
    IO_L8N_402 = Port()
    IO_L8N_H0O2P1_706 = Port()
    IO_L8N_H0O2P1_708 = Port()
    IO_L8N_H0O2P1_M0P17_700 = Port()
    IO_L8N_H0O2P1_M0P81_702 = Port()
    IO_L8N_H0O2P1_M1P145_704 = Port()
    IO_L8N_H0O2P1_M2P17_710 = Port()
    IO_L8N_H0O2P1_M2P81_712 = Port()
    IO_L8N_H0O2P1_M3P145_714 = Port()
    IO_L8P_400 = Port()
    IO_L8P_402 = Port()
    IO_L8P_H0O2P0_706 = Port()
    IO_L8P_H0O2P0_708 = Port()
    IO_L8P_H0O2P0_M0P16_700 = Port()
    IO_L8P_H0O2P0_M0P80_702 = Port()
    IO_L8P_H0O2P0_M1P144_704 = Port()
    IO_L8P_H0O2P0_M2P16_710 = Port()
    IO_L8P_H0O2P0_M2P80_712 = Port()
    IO_L8P_H0O2P0_M3P144_714 = Port()
    IO_L9N_400 = Port()
    IO_L9N_402 = Port()
    IO_L9N_XCC_H0O2P3_706 = Port()
    IO_L9N_XCC_H0O2P3_708 = Port()
    IO_L9N_XCC_H0O2P3_M0P19_700 = Port()
    IO_L9N_XCC_H0O2P3_M0P83_702 = Port()
    IO_L9N_XCC_H0O2P3_M1P147_704 = Port()
    IO_L9N_XCC_H0O2P3_M2P19_710 = Port()
    IO_L9N_XCC_H0O2P3_M2P83_712 = Port()
    IO_L9N_XCC_H0O2P3_M3P147_714 = Port()
    IO_L9P_400 = Port()
    IO_L9P_402 = Port()
    IO_L9P_XCC_H0O2P2_706 = Port()
    IO_L9P_XCC_H0O2P2_708 = Port()
    IO_L9P_XCC_H0O2P2_M0P18_700 = Port()
    IO_L9P_XCC_H0O2P2_M0P82_702 = Port()
    IO_L9P_XCC_H0O2P2_M1P146_704 = Port()
    IO_L9P_XCC_H0O2P2_M2P18_710 = Port()
    IO_L9P_XCC_H0O2P2_M2P82_712 = Port()
    IO_L9P_XCC_H0O2P2_M3P146_714 = Port()
    IO_VR_700 = Port()
    LPD_MIO0_502 = Port()
    LPD_MIO10_502 = Port()
    LPD_MIO11_502 = Port()
    LPD_MIO12_502 = Port()
    LPD_MIO13_502 = Port()
    LPD_MIO14_502 = Port()
    LPD_MIO15_502 = Port()
    LPD_MIO16_502 = Port()
    LPD_MIO17_502 = Port()
    LPD_MIO18_502 = Port()
    LPD_MIO19_502 = Port()
    LPD_MIO1_502 = Port()
    LPD_MIO20_502 = Port()
    LPD_MIO21_502 = Port()
    LPD_MIO22_502 = Port()
    LPD_MIO23_502 = Port()
    LPD_MIO24_502 = Port()
    LPD_MIO25_502 = Port()
    LPD_MIO2_502 = Port()
    LPD_MIO3_502 = Port()
    LPD_MIO4_502 = Port()
    LPD_MIO5_502 = Port()
    LPD_MIO6_502 = Port()
    LPD_MIO7_502 = Port()
    LPD_MIO8_502 = Port()
    LPD_MIO9_502 = Port()
    MIPI_REF_CLKN_507 = Port()
    MIPI_REF_CLKP_507 = Port()
    MIPI_RESREF_507 = Port()
    MIPI_RXDN0_507 = Port()
    MIPI_RXDN1_507 = Port()
    MIPI_RXDP0_507 = Port()
    MIPI_RXDP1_507 = Port()
    MIPI_TXDN0_507 = Port()
    MIPI_TXDN1_507 = Port()
    MIPI_TXDP0_507 = Port()
    MIPI_TXDP1_507 = Port()
    MODE0_503 = Port()
    MODE1_503 = Port()
    MODE2_503 = Port()
    MODE3_503 = Port()
    PMC_MIO0_500 = Port()
    PMC_MIO10_500 = Port()
    PMC_MIO11_500 = Port()
    PMC_MIO12_500 = Port()
    PMC_MIO13_500 = Port()
    PMC_MIO14_500 = Port()
    PMC_MIO15_500 = Port()
    PMC_MIO16_500 = Port()
    PMC_MIO17_500 = Port()
    PMC_MIO18_500 = Port()
    PMC_MIO19_500 = Port()
    PMC_MIO1_500 = Port()
    PMC_MIO20_500 = Port()
    PMC_MIO21_500 = Port()
    PMC_MIO22_500 = Port()
    PMC_MIO23_500 = Port()
    PMC_MIO24_500 = Port()
    PMC_MIO25_500 = Port()
    PMC_MIO26_501 = Port()
    PMC_MIO27_501 = Port()
    PMC_MIO28_501 = Port()
    PMC_MIO29_501 = Port()
    PMC_MIO2_500 = Port()
    PMC_MIO30_501 = Port()
    PMC_MIO31_501 = Port()
    PMC_MIO32_501 = Port()
    PMC_MIO33_501 = Port()
    PMC_MIO34_501 = Port()
    PMC_MIO35_501 = Port()
    PMC_MIO36_501 = Port()
    PMC_MIO37_501 = Port()
    PMC_MIO38_501 = Port()
    PMC_MIO39_501 = Port()
    PMC_MIO3_500 = Port()
    PMC_MIO40_501 = Port()
    PMC_MIO41_501 = Port()
    PMC_MIO42_501 = Port()
    PMC_MIO43_501 = Port()
    PMC_MIO44_501 = Port()
    PMC_MIO45_501 = Port()
    PMC_MIO46_501 = Port()
    PMC_MIO47_501 = Port()
    PMC_MIO48_501 = Port()
    PMC_MIO49_501 = Port()
    PMC_MIO4_500 = Port()
    PMC_MIO50_501 = Port()
    PMC_MIO51_501 = Port()
    PMC_MIO5_500 = Port()
    PMC_MIO6_500 = Port()
    PMC_MIO7_500 = Port()
    PMC_MIO8_500 = Port()
    PMC_MIO9_500 = Port()
    POR_B_503 = Port()
    PUDC_B_503 = Port()
    REF_CLK_503 = Port()
    RSVDGND = [Port() for _ in range(2)]
    RTC_PADI_503 = Port()
    RTC_PADO_503 = Port()
    TCK_503 = Port()
    TDI_503 = Port()
    TDO_503 = Port()
    TMS_503 = Port()
    USB2_DN0_504 = Port()
    USB2_DP0_504 = Port()
    USB2_ID0_504 = Port()
    USB2_TXRTUNE_504 = Port()
    USB2_VBUS0_504 = Port()
    USB3_REF_CLKN_504 = Port()
    USB3_REF_CLKP_504 = Port()
    USB3_RESREF_504 = Port()
    USB3_TXN0_504 = Port()
    USB3_TXN3_504 = Port()
    USB3_TXP0_504 = Port()
    USB3_TXP3_504 = Port()
    USB3_TXRXN1_504 = Port()
    USB3_TXRXN2_504 = Port()
    USB3_TXRXP1_504 = Port()
    USB3_TXRXP2_504 = Port()
    USB_AUXN_504 = Port()
    USB_AUXP_504 = Port()
    VCCAUX = [Port() for _ in range(18)]
    VCCAUX_LPD = [Port() for _ in range(2)]
    VCCAUX_PLL = [Port() for _ in range(4)]
    VCCAUX_SMON = Port()
    VCCINT = [Port() for _ in range(73)]
    VCCINT_SENSE = Port()
    VCCIO_MIPI_507 = [Port() for _ in range(2)]
    VCCIO_PAUX_504 = [Port() for _ in range(2)]
    VCCIO_USB2_504 = Port()
    VCCIO_USB3_504 = [Port() for _ in range(2)]
    VCCO_400 = [Port() for _ in range(2)]
    VCCO_402 = [Port() for _ in range(2)]
    VCCO_500 = [Port() for _ in range(2)]
    VCCO_501 = [Port() for _ in range(2)]
    VCCO_502 = [Port() for _ in range(2)]
    VCCO_503 = [Port() for _ in range(2)]
    VCCO_700 = [Port() for _ in range(6)]
    VCCO_705 = [Port() for _ in range(2)]
    VCCO_706 = [Port() for _ in range(2)]
    VCCO_707 = [Port() for _ in range(2)]
    VCCO_708 = [Port() for _ in range(2)]
    VCCO_709 = [Port() for _ in range(2)]
    VCCO_710 = [Port() for _ in range(2)]
    VCCO_711 = [Port() for _ in range(2)]
    VCCO_712 = [Port() for _ in range(2)]
    VCCO_713 = [Port() for _ in range(2)]
    VCCO_714 = [Port() for _ in range(2)]
    VCCO_715 = [Port() for _ in range(2)]
    VCCREG_USB2_504 = Port()
    VCC_AIE = [Port() for _ in range(89)]
    VCC_AIE_SENSE = Port()
    VCC_BATT = Port()
    VCC_FPD = [Port() for _ in range(46)]
    VCC_FPD_SENSE = Port()
    VCC_FUSE = Port()
    VCC_IO = [Port() for _ in range(7)]
    VCC_LPD = [Port() for _ in range(10)]
    VCC_MIPI_507 = [Port() for _ in range(2)]
    VCC_MMD = [Port() for _ in range(21)]
    VCC_PAUX_504 = [Port() for _ in range(2)]
    VCC_RAM = [Port() for _ in range(5)]
    VCC_SOC = [Port() for _ in range(63)]
    VCC_SOC_SENSE = Port()
    VCC_USB2_504 = [Port() for _ in range(2)]
    VCC_USB3_504 = [Port() for _ in range(2)]
    VN_500 = Port()
    VP_500 = Port()
    VREFN_500 = Port()
    VREFP_500 = Port()

    landpattern = SSVA2112BGALandpattern()
    symbol = BoxSymbol()

    mapping = [
        PadMapping(
            {
                # Row AA
                GTYP_MMI_AVCCAUX_RS[0]: landpattern.AA[10],
                GTYP_MMI_AVCCAUX_RS[1]: landpattern.AA[9],
                # Row W
                GTYP_MMI_AVCC_RS[0]: landpattern.W[10],
                # Row Y
                GTYP_MMI_AVCC_RS[1]: landpattern.Y[10],
                # Row M
                GTYP_MMI_AVTTRCAL_RS: landpattern.M[4],
                # Row W
                GTYP_MMI_AVTT_RS[0]: landpattern.W[9],
                # Row Y
                GTYP_MMI_AVTT_RS[1]: landpattern.Y[9],
                # Row L
                GTYP_MMI_REFCLKN0_105: landpattern.L[2],
                # Row K
                GTYP_MMI_REFCLKN1_105: landpattern.K[4],
                # Row L
                GTYP_MMI_REFCLKP0_105: landpattern.L[3],
                # Row K
                GTYP_MMI_REFCLKP1_105: landpattern.K[5],
                # Row M
                GTYP_MMI_RREF_RS: landpattern.M[5],
                # Row J
                GTYP_MMI_RXN0_105: landpattern.J[1],
                # Row G
                GTYP_MMI_RXN1_105: landpattern.G[1],
                # Row E
                GTYP_MMI_RXN2_105: landpattern.E[1],
                # Row C
                GTYP_MMI_RXN3_105: landpattern.C[1],
                # Row J
                GTYP_MMI_RXP0_105: landpattern.J[2],
                # Row G
                GTYP_MMI_RXP1_105: landpattern.G[2],
                # Row E
                GTYP_MMI_RXP2_105: landpattern.E[2],
                # Row C
                GTYP_MMI_RXP3_105: landpattern.C[2],
                # Row H
                GTYP_MMI_TXN0_105: landpattern.H[4],
                # Row F
                GTYP_MMI_TXN1_105: landpattern.F[4],
                # Row D
                GTYP_MMI_TXN2_105: landpattern.D[4],
                # Row B
                GTYP_MMI_TXN3_105: landpattern.B[4],
                # Row H
                GTYP_MMI_TXP0_105: landpattern.H[5],
                # Row F
                GTYP_MMI_TXP1_105: landpattern.F[5],
                # Row D
                GTYP_MMI_TXP2_105: landpattern.D[5],
                # Row B
                GTYP_MMI_TXP3_105: landpattern.B[5],
                # Row F
                GTYP_REFCLKN0_106: landpattern.F[7],
                # Row K
                GTYP_REFCLKN1_106: landpattern.K[7],
                # Row G
                GTYP_REFCLKP0_106: landpattern.G[7],
                # Row L
                GTYP_REFCLKP1_106: landpattern.L[7],
                # Row A
                GTYP_RXN0_106: landpattern.A[7],
                GTYP_RXN1_106: landpattern.A[9],
                GTYP_RXN2_106: landpattern.A[11],
                GTYP_RXN3_106: landpattern.A[13],
                # Row B
                GTYP_RXP0_106: landpattern.B[7],
                GTYP_RXP1_106: landpattern.B[9],
                GTYP_RXP2_106: landpattern.B[11],
                GTYP_RXP3_106: landpattern.B[13],
                # Row D
                GTYP_TXN0_106: landpattern.D[8],
                GTYP_TXN1_106: landpattern.D[10],
                GTYP_TXN2_106: landpattern.D[12],
                GTYP_TXN3_106: landpattern.D[14],
                # Row E
                GTYP_TXP0_106: landpattern.E[8],
                GTYP_TXP1_106: landpattern.E[10],
                GTYP_TXP2_106: landpattern.E[12],
                GTYP_TXP3_106: landpattern.E[14],
                # Row H
                GTYP_AVTTRCAL_RN: landpattern.H[8],
                # Row F
                GTYP_REFCLKN0_107: landpattern.F[9],
                # Row H
                GTYP_REFCLKN1_107: landpattern.H[10],
                # Row G
                GTYP_REFCLKP0_107: landpattern.G[9],
                # Row J
                GTYP_REFCLKP1_107: landpattern.J[10],
                GTYP_RREF_RN: landpattern.J[8],
                # Row A
                GTYP_RXN0_107: landpattern.A[15],
                GTYP_RXN1_107: landpattern.A[17],
                GTYP_RXN2_107: landpattern.A[19],
                GTYP_RXN3_107: landpattern.A[21],
                # Row B
                GTYP_RXP0_107: landpattern.B[15],
                GTYP_RXP1_107: landpattern.B[17],
                GTYP_RXP2_107: landpattern.B[19],
                GTYP_RXP3_107: landpattern.B[21],
                # Row D
                GTYP_TXN0_107: landpattern.D[16],
                GTYP_TXN1_107: landpattern.D[18],
                GTYP_TXN2_107: landpattern.D[20],
                GTYP_TXN3_107: landpattern.D[22],
                # Row E
                GTYP_TXP0_107: landpattern.E[16],
                GTYP_TXP1_107: landpattern.E[18],
                GTYP_TXP2_107: landpattern.E[20],
                GTYP_TXP3_107: landpattern.E[22],
                # Row P
                GTYP_AVTTRCAL_L: landpattern.P[39],
                # Row N
                GTYP_REFCLKN0_205: landpattern.N[41],
                # Row M
                GTYP_REFCLKN1_205: landpattern.M[39],
                # Row N
                GTYP_REFCLKP0_205: landpattern.N[40],
                # Row M
                GTYP_REFCLKP1_205: landpattern.M[38],
                # Row P
                GTYP_RREF_L: landpattern.P[38],
                # Row N
                GTYP_RXN0_205: landpattern.N[46],
                # Row L
                GTYP_RXN1_205: landpattern.L[46],
                # Row J
                GTYP_RXN2_205: landpattern.J[46],
                # Row G
                GTYP_RXN3_205: landpattern.G[46],
                # Row N
                GTYP_RXP0_205: landpattern.N[45],
                # Row L
                GTYP_RXP1_205: landpattern.L[45],
                # Row J
                GTYP_RXP2_205: landpattern.J[45],
                # Row G
                GTYP_RXP3_205: landpattern.G[45],
                # Row P
                GTYP_TXN0_205: landpattern.P[43],
                # Row M
                GTYP_TXN1_205: landpattern.M[43],
                # Row K
                GTYP_TXN2_205: landpattern.K[43],
                # Row H
                GTYP_TXN3_205: landpattern.H[43],
                # Row P
                GTYP_TXP0_205: landpattern.P[42],
                # Row M
                GTYP_TXP1_205: landpattern.M[42],
                # Row K
                GTYP_TXP2_205: landpattern.K[42],
                # Row H
                GTYP_TXP3_205: landpattern.H[42],
                # Row L
                GTYP_REFCLKN0_206: landpattern.L[41],
                # Row K
                GTYP_REFCLKN1_206: landpattern.K[39],
                # Row L
                GTYP_REFCLKP0_206: landpattern.L[40],
                # Row K
                GTYP_REFCLKP1_206: landpattern.K[38],
                # Row A
                GTYP_RXN0_206: landpattern.A[44],
                GTYP_RXN1_206: landpattern.A[42],
                GTYP_RXN2_206: landpattern.A[40],
                GTYP_RXN3_206: landpattern.A[38],
                # Row B
                GTYP_RXP0_206: landpattern.B[44],
                GTYP_RXP1_206: landpattern.B[42],
                GTYP_RXP2_206: landpattern.B[40],
                GTYP_RXP3_206: landpattern.B[38],
                # Row D
                GTYP_TXN0_206: landpattern.D[45],
                GTYP_TXN1_206: landpattern.D[43],
                GTYP_TXN2_206: landpattern.D[41],
                GTYP_TXN3_206: landpattern.D[39],
                # Row E
                GTYP_TXP0_206: landpattern.E[45],
                GTYP_TXP1_206: landpattern.E[43],
                GTYP_TXP2_206: landpattern.E[41],
                GTYP_TXP3_206: landpattern.E[39],
                # Row J
                GTYP_REFCLKN0_207: landpattern.J[41],
                # Row G
                GTYP_REFCLKN1_207: landpattern.G[41],
                # Row J
                GTYP_REFCLKP0_207: landpattern.J[40],
                # Row G
                GTYP_REFCLKP1_207: landpattern.G[40],
                # Row A
                GTYP_RXN0_207: landpattern.A[36],
                GTYP_RXN1_207: landpattern.A[34],
                GTYP_RXN2_207: landpattern.A[32],
                GTYP_RXN3_207: landpattern.A[30],
                # Row B
                GTYP_RXP0_207: landpattern.B[36],
                GTYP_RXP1_207: landpattern.B[34],
                GTYP_RXP2_207: landpattern.B[32],
                GTYP_RXP3_207: landpattern.B[30],
                # Row D
                GTYP_TXN0_207: landpattern.D[37],
                GTYP_TXN1_207: landpattern.D[35],
                GTYP_TXN2_207: landpattern.D[33],
                GTYP_TXN3_207: landpattern.D[31],
                # Row E
                GTYP_TXP0_207: landpattern.E[37],
                GTYP_TXP1_207: landpattern.E[35],
                GTYP_TXP2_207: landpattern.E[33],
                GTYP_TXP3_207: landpattern.E[31],
                # Row V
                IO_L0N_400: landpattern.V[46],
                # Row W
                IO_L0P_400: landpattern.W[46],
                IO_L10N_400: landpattern.W[38],
                # Row Y
                IO_L10P_400: landpattern.Y[38],
                IO_L1N_400: landpattern.Y[46],
                IO_L1P_400: landpattern.Y[45],
                # Row AA
                IO_L2N_400: landpattern.AA[45],
                IO_L2P_400: landpattern.AA[44],
                # Row W
                IO_L3N_400: landpattern.W[45],
                IO_L3P_400: landpattern.W[44],
                IO_L4N_400: landpattern.W[43],
                # Row Y
                IO_L4P_400: landpattern.Y[43],
                # Row AA
                IO_L5N_HDGC_400: landpattern.AA[43],
                IO_L5P_HDGC_400: landpattern.AA[42],
                # Row Y
                IO_L6N_HDGC_400: landpattern.Y[42],
                IO_L6P_HDGC_400: landpattern.Y[41],
                # Row W
                IO_L7N_400: landpattern.W[41],
                # Row Y
                IO_L7P_400: landpattern.Y[40],
                # Row AA
                IO_L8N_400: landpattern.AA[40],
                IO_L8P_400: landpattern.AA[39],
                # Row W
                IO_L9N_400: landpattern.W[40],
                IO_L9P_400: landpattern.W[39],
                # Row AL
                VCCO_400[0]: landpattern.AL[32],
                # Row AM
                VCCO_400[1]: landpattern.AM[32],
                # Row R
                IO_L0N_402: landpattern.R[46],
                IO_L0P_402: landpattern.R[45],
                # Row T
                IO_L10N_402: landpattern.T[39],
                IO_L10P_402: landpattern.T[38],
                # Row U
                IO_L1N_402: landpattern.U[46],
                IO_L1P_402: landpattern.U[45],
                # Row T
                IO_L2N_402: landpattern.T[45],
                IO_L2P_402: landpattern.T[44],
                # Row U
                IO_L3N_402: landpattern.U[44],
                # Row V
                IO_L3P_402: landpattern.V[44],
                IO_L4N_402: landpattern.V[43],
                IO_L4P_402: landpattern.V[42],
                # Row T
                IO_L5N_HDGC_402: landpattern.T[43],
                IO_L5P_HDGC_402: landpattern.T[42],
                # Row U
                IO_L6N_HDGC_402: landpattern.U[42],
                # Row V
                IO_L6P_HDGC_402: landpattern.V[41],
                # Row U
                IO_L7N_402: landpattern.U[41],
                IO_L7P_402: landpattern.U[40],
                # Row T
                IO_L8N_402: landpattern.T[40],
                # Row U
                IO_L8P_402: landpattern.U[39],
                # Row V
                IO_L9N_402: landpattern.V[39],
                IO_L9P_402: landpattern.V[38],
                # Row AE
                VCCO_402[0]: landpattern.AE[32],
                # Row AF
                VCCO_402[1]: landpattern.AF[32],
                # Row G
                PMC_MIO0_500: landpattern.G[38],
                # Row J
                PMC_MIO10_500: landpattern.J[34],
                PMC_MIO11_500: landpattern.J[33],
                # Row G
                PMC_MIO12_500: landpattern.G[33],
                PMC_MIO13_500: landpattern.G[32],
                # Row H
                PMC_MIO14_500: landpattern.H[32],
                # Row J
                PMC_MIO15_500: landpattern.J[32],
                PMC_MIO16_500: landpattern.J[31],
                # Row H
                PMC_MIO17_500: landpattern.H[31],
                # Row G
                PMC_MIO18_500: landpattern.G[30],
                # Row H
                PMC_MIO19_500: landpattern.H[30],
                PMC_MIO1_500: landpattern.H[38],
                # Row J
                PMC_MIO20_500: landpattern.J[29],
                # Row H
                PMC_MIO21_500: landpattern.H[29],
                # Row G
                PMC_MIO22_500: landpattern.G[29],
                PMC_MIO23_500: landpattern.G[28],
                # Row J
                PMC_MIO24_500: landpattern.J[28],
                PMC_MIO25_500: landpattern.J[27],
                # Row H
                PMC_MIO2_500: landpattern.H[37],
                # Row G
                PMC_MIO3_500: landpattern.G[37],
                # Row H
                PMC_MIO4_500: landpattern.H[36],
                # Row J
                PMC_MIO5_500: landpattern.J[36],
                # Row H
                PMC_MIO6_500: landpattern.H[35],
                # Row G
                PMC_MIO7_500: landpattern.G[35],
                PMC_MIO8_500: landpattern.G[34],
                # Row H
                PMC_MIO9_500: landpattern.H[34],
                # Row AH
                VCCO_500[0]: landpattern.AH[11],
                # Row AJ
                VCCO_500[1]: landpattern.AJ[11],
                # Row H
                PMC_MIO26_501: landpattern.H[27],
                # Row G
                PMC_MIO27_501: landpattern.G[27],
                # Row F
                PMC_MIO28_501: landpattern.F[26],
                # Row H
                PMC_MIO29_501: landpattern.H[26],
                # Row J
                PMC_MIO30_501: landpattern.J[26],
                # Row H
                PMC_MIO31_501: landpattern.H[25],
                # Row G
                PMC_MIO32_501: landpattern.G[25],
                # Row F
                PMC_MIO33_501: landpattern.F[25],
                # Row G
                PMC_MIO34_501: landpattern.G[24],
                # Row H
                PMC_MIO35_501: landpattern.H[24],
                # Row J
                PMC_MIO36_501: landpattern.J[24],
                PMC_MIO37_501: landpattern.J[23],
                # Row G
                PMC_MIO38_501: landpattern.G[23],
                PMC_MIO39_501: landpattern.G[22],
                # Row H
                PMC_MIO40_501: landpattern.H[22],
                # Row J
                PMC_MIO41_501: landpattern.J[22],
                PMC_MIO42_501: landpattern.J[21],
                # Row H
                PMC_MIO43_501: landpattern.H[21],
                # Row G
                PMC_MIO44_501: landpattern.G[20],
                # Row H
                PMC_MIO45_501: landpattern.H[20],
                # Row J
                PMC_MIO46_501: landpattern.J[19],
                # Row H
                PMC_MIO47_501: landpattern.H[19],
                # Row G
                PMC_MIO48_501: landpattern.G[19],
                PMC_MIO49_501: landpattern.G[18],
                # Row J
                PMC_MIO50_501: landpattern.J[18],
                # Row G
                PMC_MIO51_501: landpattern.G[17],
                # Row AK
                VCCO_501[0]: landpattern.AK[12],
                # Row AL
                VCCO_501[1]: landpattern.AL[12],
                # Row D
                LPD_MIO0_502: landpattern.D[29],
                LPD_MIO10_502: landpattern.D[27],
                # Row F
                LPD_MIO11_502: landpattern.F[27],
                # Row E
                LPD_MIO12_502: landpattern.E[26],
                # Row D
                LPD_MIO13_502: landpattern.D[26],
                # Row C
                LPD_MIO14_502: landpattern.C[26],
                # Row A
                LPD_MIO15_502: landpattern.A[26],
                LPD_MIO16_502: landpattern.A[25],
                # Row B
                LPD_MIO17_502: landpattern.B[25],
                # Row C
                LPD_MIO18_502: landpattern.C[25],
                # Row E
                LPD_MIO19_502: landpattern.E[25],
                LPD_MIO1_502: landpattern.E[29],
                LPD_MIO20_502: landpattern.E[24],
                # Row D
                LPD_MIO21_502: landpattern.D[24],
                # Row C
                LPD_MIO22_502: landpattern.C[24],
                # Row B
                LPD_MIO23_502: landpattern.B[24],
                # Row A
                LPD_MIO24_502: landpattern.A[23],
                # Row B
                LPD_MIO25_502: landpattern.B[23],
                # Row F
                LPD_MIO2_502: landpattern.F[28],
                # Row E
                LPD_MIO3_502: landpattern.E[28],
                # Row D
                LPD_MIO4_502: landpattern.D[28],
                # Row B
                LPD_MIO5_502: landpattern.B[28],
                # Row A
                LPD_MIO6_502: landpattern.A[28],
                LPD_MIO7_502: landpattern.A[27],
                # Row B
                LPD_MIO8_502: landpattern.B[27],
                # Row C
                LPD_MIO9_502: landpattern.C[27],
                # Row AE
                VCCO_502[0]: landpattern.AE[11],
                # Row AF
                VCCO_502[1]: landpattern.AF[11],
                # Row H
                DONE_503: landpattern.H[17],
                # Row J
                ERROR_OUT_503: landpattern.J[17],
                # Row H
                I3CI2C_SCL_503: landpattern.H[16],
                # Row J
                I3CI2C_SDA_503: landpattern.J[16],
                MODE0_503: landpattern.J[14],
                # Row G
                MODE1_503: landpattern.G[13],
                # Row J
                MODE2_503: landpattern.J[13],
                # Row G
                MODE3_503: landpattern.G[12],
                # Row AK
                POR_B_503: landpattern.AK[18],
                # Row H
                PUDC_B_503: landpattern.H[12],
                # Row AL
                REF_CLK_503: landpattern.AL[17],
                # Row J
                RTC_PADI_503: landpattern.J[12],
                # Row K
                RTC_PADO_503: landpattern.K[12],
                # Row G
                TCK_503: landpattern.G[15],
                # Row H
                TDI_503: landpattern.H[15],
                # Row G
                TDO_503: landpattern.G[14],
                # Row H
                TMS_503: landpattern.H[14],
                # Row AN
                VCCO_503[0]: landpattern.AN[12],
                # Row AP
                VCCO_503[1]: landpattern.AP[12],
                # Row P
                USB_AUXN_504: landpattern.P[4],
                USB_AUXP_504: landpattern.P[5],
                # Row N
                USB2_DN0_504: landpattern.N[2],
                USB2_DP0_504: landpattern.N[3],
                # Row M
                USB2_ID0_504: landpattern.M[6],
                USB2_TXRTUNE_504: landpattern.M[8],
                # Row N
                USB2_VBUS0_504: landpattern.N[6],
                # Row U
                USB3_REF_CLKN_504: landpattern.U[6],
                USB3_REF_CLKP_504: landpattern.U[7],
                # Row R
                USB3_RESREF_504: landpattern.R[6],
                # Row V
                USB3_TXN0_504: landpattern.V[4],
                USB3_TXP0_504: landpattern.V[5],
                # Row T
                USB3_TXN3_504: landpattern.T[4],
                USB3_TXP3_504: landpattern.T[5],
                # Row R
                USB3_TXRXN1_504: landpattern.R[1],
                USB3_TXRXP1_504: landpattern.R[2],
                # Row U
                USB3_TXRXN2_504: landpattern.U[1],
                USB3_TXRXP2_504: landpattern.U[2],
                # Row AA
                VCCIO_PAUX_504[0]: landpattern.AA[12],
                # Row AB
                VCCIO_PAUX_504[1]: landpattern.AB[12],
                # Row AE
                VCCIO_USB2_504: landpattern.AE[8],
                # Row AC
                VCCIO_USB3_504[0]: landpattern.AC[10],
                # Row AD
                VCCIO_USB3_504[1]: landpattern.AD[10],
                # Row AF
                VCCREG_USB2_504: landpattern.AF[8],
                # Row AD
                VCC_PAUX_504[0]: landpattern.AD[9],
                # Row AE
                VCC_PAUX_504[1]: landpattern.AE[9],
                # Row AC
                VCC_USB2_504[0]: landpattern.AC[11],
                VCC_USB2_504[1]: landpattern.AC[13],
                # Row AD
                VCC_USB3_504[0]: landpattern.AD[12],
                VCC_USB3_504[1]: landpattern.AD[13],
                # Row AA
                MIPI_REF_CLKN_507: landpattern.AA[6],
                MIPI_REF_CLKP_507: landpattern.AA[7],
                # Row W
                MIPI_RESREF_507: landpattern.W[6],
                # Row AA
                MIPI_RXDN0_507: landpattern.AA[1],
                # Row W
                MIPI_RXDN1_507: landpattern.W[1],
                # Row AA
                MIPI_RXDP0_507: landpattern.AA[2],
                # Row W
                MIPI_RXDP1_507: landpattern.W[2],
                # Row AB
                MIPI_TXDN0_507: landpattern.AB[4],
                # Row Y
                MIPI_TXDN1_507: landpattern.Y[4],
                # Row AB
                MIPI_TXDP0_507: landpattern.AB[5],
                # Row Y
                MIPI_TXDP1_507: landpattern.Y[5],
                # Row AJ
                VCCIO_MIPI_507[0]: landpattern.AJ[13],
                VCCIO_MIPI_507[1]: landpattern.AJ[14],
                # Row AK
                VCC_MIPI_507[0]: landpattern.AK[13],
                VCC_MIPI_507[1]: landpattern.AK[15],
                # Row AF
                IO_L0N_H0O0P1_M0P1_700: landpattern.AF[2],
                # Row AG
                IO_L0P_H0O0P0_M0P0_700: landpattern.AG[3],
                IO_L10N_H0O2P5_M0P21_700: landpattern.AG[6],
                # Row AF
                IO_L10P_H0O2P4_M0P20_700: landpattern.AF[7],
                # Row AD
                IO_L11N_H0O2P7_M0P23_700: landpattern.AD[6],
                IO_L11P_H0O2P6_M0P22_700: landpattern.AD[7],
                # Row AG
                IO_L12N_H0O3P1_M0P25_700: landpattern.AG[7],
                # Row AH
                IO_L12P_H0O3P0_M0P24_700: landpattern.AH[8],
                # Row AC
                IO_L13N_XCC_H0O3P3_M0P27_700: landpattern.AC[7],
                IO_L13P_XCC_H0O3P2_M0P26_700: landpattern.AC[8],
                # Row AG
                IO_L14N_H0O3P5_M0P29_700: landpattern.AG[10],
                # Row AF
                IO_L14P_H0O3P4_M0P28_700: landpattern.AF[10],
                # Row AH
                IO_L15N_H0O3P7_M0P31_700: landpattern.AH[9],
                # Row AG
                IO_L15P_H0O3P6_M0P30_700: landpattern.AG[9],
                # Row AC
                IO_L1N_XCC_H0O0P3_M0P3_700: landpattern.AC[1],
                IO_L1P_XCC_H0O0P2_M0P2_700: landpattern.AC[2],
                # Row AE
                IO_L2N_H0O0P5_M0P5_700: landpattern.AE[1],
                # Row AD
                IO_L2P_H0O0P4_M0P4_700: landpattern.AD[1],
                # Row AG
                IO_L3N_GC_H0O0P7_M0P7_700: landpattern.AG[1],
                # Row AF
                IO_L3P_GC_H0O0P6_M0P6_700: landpattern.AF[1],
                # Row AD
                IO_L4N_H0O1P1_M0P9_700: landpattern.AD[3],
                IO_L4P_H0O1P0_M0P8_700: landpattern.AD[4],
                # Row AE
                IO_L5N_XCC_H0O1P3_M0P11_700: landpattern.AE[2],
                IO_L5P_XCC_H0O1P2_M0P10_700: landpattern.AE[3],
                # Row AH
                IO_L6N_H0O1P5_M0P13_700: landpattern.AH[3],
                # Row AG
                IO_L6P_H0O1P4_M0P12_700: landpattern.AG[4],
                # Row AF
                IO_L7N_H0O1P7_M0P15_700: landpattern.AF[4],
                IO_L7P_H0O1P6_M0P14_700: landpattern.AF[5],
                # Row AE
                IO_L8N_H0O2P1_M0P17_700: landpattern.AE[5],
                IO_L8P_H0O2P0_M0P16_700: landpattern.AE[6],
                # Row AH
                IO_L9N_XCC_H0O2P3_M0P19_700: landpattern.AH[5],
                IO_L9P_XCC_H0O2P2_M0P18_700: landpattern.AH[6],
                # Row AP
                IO_VR_700: landpattern.AP[14],
                # Row AM
                IO_L16N_H1O0P1_M0P33_701: landpattern.AM[11],
                # Row AL
                IO_L16P_H1O0P0_M0P32_701: landpattern.AL[11],
                IO_L17N_XCC_H1O0P3_M0P35_701: landpattern.AL[9],
                # Row AM
                IO_L17P_XCC_H1O0P2_M0P34_701: landpattern.AM[10],
                # Row AK
                IO_L18N_H1O0P5_M0P37_701: landpattern.AK[10],
                # Row AJ
                IO_L18P_H1O0P4_M0P36_701: landpattern.AJ[10],
                # Row AL
                IO_L19N_GC_H1O0P7_M0P39_701: landpattern.AL[8],
                # Row AK
                IO_L19P_GC_H1O0P6_M0P38_701: landpattern.AK[9],
                # Row AJ
                IO_L20N_H1O1P1_M0P41_701: landpattern.AJ[7],
                IO_L20P_H1O1P0_M0P40_701: landpattern.AJ[8],
                # Row AM
                IO_L21N_XCC_H1O1P3_M0P43_701: landpattern.AM[7],
                IO_L21P_XCC_H1O1P2_M0P42_701: landpattern.AM[8],
                # Row AK
                IO_L22N_H1O1P5_M0P45_701: landpattern.AK[6],
                IO_L22P_H1O1P4_M0P44_701: landpattern.AK[7],
                # Row AJ
                IO_L23N_H1O1P7_M0P47_701: landpattern.AJ[4],
                IO_L23P_H1O1P6_M0P46_701: landpattern.AJ[5],
                # Row AM
                IO_L24N_H1O2P1_M0P49_701: landpattern.AM[4],
                IO_L24P_H1O2P0_M0P48_701: landpattern.AM[5],
                # Row AL
                IO_L25N_XCC_H1O2P3_M0P51_701: landpattern.AL[5],
                IO_L25P_XCC_H1O2P2_M0P50_701: landpattern.AL[6],
                # Row AH
                IO_L26N_H1O2P5_M0P53_701: landpattern.AH[1],
                IO_L26P_H1O2P4_M0P52_701: landpattern.AH[2],
                # Row AJ
                IO_L27N_H1O2P7_M0P55_701: landpattern.AJ[1],
                IO_L27P_H1O2P6_M0P54_701: landpattern.AJ[2],
                # Row AL
                IO_L28N_H1O3P1_M0P57_701: landpattern.AL[1],
                # Row AK
                IO_L28P_H1O3P0_M0P56_701: landpattern.AK[1],
                IO_L29N_XCC_H1O3P3_M0P59_701: landpattern.AK[3],
                IO_L29P_XCC_H1O3P2_M0P58_701: landpattern.AK[4],
                # Row AL
                IO_L30N_H1O3P5_M0P61_701: landpattern.AL[2],
                IO_L30P_H1O3P4_M0P60_701: landpattern.AL[3],
                # Row AM
                IO_L31N_H1O3P7_M0P63_701: landpattern.AM[1],
                IO_L31P_H1O3P6_M0P62_701: landpattern.AM[2],
                # Row AP
                IO_L0N_H0O0P1_M0P65_702: landpattern.AP[1],
                # Row AN
                IO_L0P_H0O0P0_M0P64_702: landpattern.AN[1],
                # Row AP
                IO_L10N_H0O2P5_M0P85_702: landpattern.AP[8],
                IO_L10P_H0O2P4_M0P84_702: landpattern.AP[9],
                # Row AT
                IO_L11N_H0O2P7_M0P87_702: landpattern.AT[10],
                # Row AR
                IO_L11P_H0O2P6_M0P86_702: landpattern.AR[10],
                # Row AN
                IO_L12N_H0O3P1_M0P89_702: landpattern.AN[9],
                IO_L12P_H0O3P0_M0P88_702: landpattern.AN[10],
                # Row AR
                IO_L13N_XCC_H0O3P3_M0P91_702: landpattern.AR[11],
                # Row AP
                IO_L13P_XCC_H0O3P2_M0P90_702: landpattern.AP[11],
                # Row AT
                IO_L14N_H0O3P5_M0P93_702: landpattern.AT[12],
                # Row AR
                IO_L14P_H0O3P4_M0P92_702: landpattern.AR[13],
                # Row AT
                IO_L15N_H0O3P7_M0P95_702: landpattern.AT[13],
                # Row AU
                IO_L15P_H0O3P6_M0P94_702: landpattern.AU[14],
                # Row AR
                IO_L1N_XCC_H0O0P3_M0P67_702: landpattern.AR[1],
                IO_L1P_XCC_H0O0P2_M0P66_702: landpattern.AR[2],
                # Row AN
                IO_L2N_H0O0P5_M0P69_702: landpattern.AN[3],
                IO_L2P_H0O0P4_M0P68_702: landpattern.AN[4],
                # Row AP
                IO_L3N_GC_H0O0P7_M0P71_702: landpattern.AP[2],
                IO_L3P_GC_H0O0P6_M0P70_702: landpattern.AP[3],
                # Row AT
                IO_L4N_H0O1P1_M0P73_702: landpattern.AT[4],
                # Row AR
                IO_L4P_H0O1P0_M0P72_702: landpattern.AR[4],
                IO_L5N_XCC_H0O1P3_M0P75_702: landpattern.AR[5],
                # Row AP
                IO_L5P_XCC_H0O1P2_M0P74_702: landpattern.AP[5],
                # Row AT
                IO_L6N_H0O1P5_M0P77_702: landpattern.AT[6],
                IO_L6P_H0O1P4_M0P76_702: landpattern.AT[7],
                # Row AP
                IO_L7N_H0O1P7_M0P79_702: landpattern.AP[6],
                # Row AR
                IO_L7P_H0O1P6_M0P78_702: landpattern.AR[7],
                # Row AN
                IO_L8N_H0O2P1_M0P81_702: landpattern.AN[6],
                IO_L8P_H0O2P0_M0P80_702: landpattern.AN[7],
                # Row AR
                IO_L9N_XCC_H0O2P3_M0P83_702: landpattern.AR[8],
                # Row AT
                IO_L9P_XCC_H0O2P2_M0P82_702: landpattern.AT[9],
                # Row AW
                IO_L16N_H1O0P1_M1P97_703: landpattern.AW[12],
                IO_L16P_H1O0P0_M1P96_703: landpattern.AW[13],
                # Row AU
                IO_L17N_XCC_H1O0P3_M1P99_703: landpattern.AU[11],
                IO_L17P_XCC_H1O0P2_M1P98_703: landpattern.AU[12],
                # Row AV
                IO_L18N_H1O0P5_M1P101_703: landpattern.AV[10],
                IO_L18P_H1O0P4_M1P100_703: landpattern.AV[11],
                # Row AW
                IO_L19N_GC_H1O0P7_M1P103_703: landpattern.AW[9],
                IO_L19P_GC_H1O0P6_M1P102_703: landpattern.AW[10],
                # Row AU
                IO_L20N_H1O1P1_M1P105_703: landpattern.AU[8],
                IO_L20P_H1O1P0_M1P104_703: landpattern.AU[9],
                # Row AV
                IO_L21N_XCC_H1O1P3_M1P107_703: landpattern.AV[7],
                IO_L21P_XCC_H1O1P2_M1P106_703: landpattern.AV[8],
                # Row AW
                IO_L22N_H1O1P5_M1P109_703: landpattern.AW[6],
                IO_L22P_H1O1P4_M1P108_703: landpattern.AW[7],
                # Row AU
                IO_L23N_H1O1P7_M1P111_703: landpattern.AU[5],
                IO_L23P_H1O1P6_M1P110_703: landpattern.AU[6],
                # Row AW
                IO_L24N_H1O2P1_M1P113_703: landpattern.AW[4],
                # Row AY
                IO_L24P_H1O2P0_M1P112_703: landpattern.AY[5],
                # Row AV
                IO_L25N_XCC_H1O2P3_M1P115_703: landpattern.AV[4],
                IO_L25P_XCC_H1O2P2_M1P114_703: landpattern.AV[5],
                # Row AY
                IO_L26N_H1O2P5_M1P117_703: landpattern.AY[3],
                # Row AW
                IO_L26P_H1O2P4_M1P116_703: landpattern.AW[3],
                # Row AV
                IO_L27N_H1O2P7_M1P119_703: landpattern.AV[2],
                # Row AU
                IO_L27P_H1O2P6_M1P118_703: landpattern.AU[2],
                IO_L28N_H1O3P1_M1P121_703: landpattern.AU[3],
                # Row AT
                IO_L28P_H1O3P0_M1P120_703: landpattern.AT[3],
                # Row AY
                IO_L29N_XCC_H1O3P3_M1P123_703: landpattern.AY[1],
                IO_L29P_XCC_H1O3P2_M1P122_703: landpattern.AY[2],
                # Row AW
                IO_L30N_H1O3P5_M1P125_703: landpattern.AW[1],
                # Row AV
                IO_L30P_H1O3P4_M1P124_703: landpattern.AV[1],
                # Row AU
                IO_L31N_H1O3P7_M1P127_703: landpattern.AU[1],
                # Row AT
                IO_L31P_H1O3P6_M1P126_703: landpattern.AT[1],
                # Row BB
                IO_L0N_H0O0P1_M1P129_704: landpattern.BB[1],
                # Row BA
                IO_L0P_H0O0P0_M1P128_704: landpattern.BA[1],
                # Row BB
                IO_L10N_H0O2P5_M1P149_704: landpattern.BB[9],
                IO_L10P_H0O2P4_M1P148_704: landpattern.BB[10],
                # Row BA
                IO_L11N_H0O2P7_M1P151_704: landpattern.BA[10],
                IO_L11P_H0O2P6_M1P150_704: landpattern.BA[11],
                # Row AY
                IO_L12N_H0O3P1_M1P153_704: landpattern.AY[11],
                IO_L12P_H0O3P0_M1P152_704: landpattern.AY[12],
                # Row BB
                IO_L13N_XCC_H0O3P3_M1P155_704: landpattern.BB[13],
                # Row BA
                IO_L13P_XCC_H0O3P2_M1P154_704: landpattern.BA[13],
                # Row BC
                IO_L14N_H0O3P5_M1P157_704: landpattern.BC[11],
                # Row BB
                IO_L14P_H0O3P4_M1P156_704: landpattern.BB[12],
                # Row BA
                IO_L15N_H0O3P7_M1P159_704: landpattern.BA[14],
                # Row AY
                IO_L15P_H0O3P6_M1P158_704: landpattern.AY[14],
                # Row BC
                IO_L1N_XCC_H0O0P3_M1P131_704: landpattern.BC[1],
                IO_L1P_XCC_H0O0P2_M1P130_704: landpattern.BC[2],
                # Row BA
                IO_L2N_H0O0P5_M1P133_704: landpattern.BA[2],
                # Row BB
                IO_L2P_H0O0P4_M1P132_704: landpattern.BB[3],
                # Row BA
                IO_L3N_GC_H0O0P7_M1P135_704: landpattern.BA[5],
                # Row AY
                IO_L3P_GC_H0O0P6_M1P134_704: landpattern.AY[6],
                # Row BB
                IO_L4N_H0O1P1_M1P137_704: landpattern.BB[4],
                # Row BA
                IO_L4P_H0O1P0_M1P136_704: landpattern.BA[4],
                # Row BC
                IO_L5N_XCC_H0O1P3_M1P139_704: landpattern.BC[5],
                IO_L5P_XCC_H0O1P2_M1P138_704: landpattern.BC[6],
                # Row BB
                IO_L6N_H0O1P5_M1P141_704: landpattern.BB[6],
                IO_L6P_H0O1P4_M1P140_704: landpattern.BB[7],
                # Row BC
                IO_L7N_H0O1P7_M1P143_704: landpattern.BC[8],
                IO_L7P_H0O1P6_M1P142_704: landpattern.BC[9],
                # Row BA
                IO_L8N_H0O2P1_M1P145_704: landpattern.BA[7],
                IO_L8P_H0O2P0_M1P144_704: landpattern.BA[8],
                # Row AY
                IO_L9N_XCC_H0O2P3_M1P147_704: landpattern.AY[8],
                IO_L9P_XCC_H0O2P2_M1P146_704: landpattern.AY[9],
                # Row BC
                IO_L16N_H1O0P1_M1P161_705: landpattern.BC[12],
                # Row BD
                IO_L16P_H1O0P0_M1P160_705: landpattern.BD[13],
                # Row BE
                IO_L17N_XCC_H1O0P3_M1P163_705: landpattern.BE[13],
                # Row BD
                IO_L17P_XCC_H1O0P2_M1P162_705: landpattern.BD[14],
                IO_L18N_H1O0P5_M1P165_705: landpattern.BD[11],
                # Row BE
                IO_L18P_H1O0P4_M1P164_705: landpattern.BE[12],
                # Row BF
                IO_L19N_GC_H1O0P7_M1P167_705: landpattern.BF[11],
                IO_L19P_GC_H1O0P6_M1P166_705: landpattern.BF[12],
                IO_L20N_H1O1P1_M1P169_705: landpattern.BF[13],
                IO_L20P_H1O1P0_M1P168_705: landpattern.BF[14],
                # Row BE
                IO_L21N_XCC_H1O1P3_M1P171_705: landpattern.BE[10],
                # Row BD
                IO_L21P_XCC_H1O1P2_M1P170_705: landpattern.BD[10],
                # Row BF
                IO_L22N_H1O1P5_M1P173_705: landpattern.BF[7],
                IO_L22P_H1O1P4_M1P172_705: landpattern.BF[8],
                IO_L23N_H1O1P7_M1P175_705: landpattern.BF[9],
                IO_L23P_H1O1P6_M1P174_705: landpattern.BF[10],
                # Row BD
                IO_L24N_H1O2P1_M1P177_705: landpattern.BD[8],
                # Row BE
                IO_L24P_H1O2P0_M1P176_705: landpattern.BE[9],
                IO_L25N_XCC_H1O2P3_M1P179_705: landpattern.BE[7],
                # Row BD
                IO_L25P_XCC_H1O2P2_M1P178_705: landpattern.BD[7],
                IO_L26N_H1O2P5_M1P181_705: landpattern.BD[5],
                # Row BE
                IO_L26P_H1O2P4_M1P180_705: landpattern.BE[6],
                # Row BF
                IO_L27N_H1O2P7_M1P183_705: landpattern.BF[5],
                IO_L27P_H1O2P6_M1P182_705: landpattern.BF[6],
                IO_L28N_H1O3P1_M1P185_705: landpattern.BF[3],
                # Row BE
                IO_L28P_H1O3P0_M1P184_705: landpattern.BE[3],
                # Row BF
                IO_L29N_XCC_H1O3P3_M1P187_705: landpattern.BF[4],
                # Row BE
                IO_L29P_XCC_H1O3P2_M1P186_705: landpattern.BE[4],
                # Row BD
                IO_L30N_H1O3P5_M1P189_705: landpattern.BD[1],
                IO_L30P_H1O3P4_M1P188_705: landpattern.BD[2],
                # Row BC
                IO_L31N_H1O3P7_M1P191_705: landpattern.BC[3],
                # Row BD
                IO_L31P_H1O3P6_M1P190_705: landpattern.BD[4],
                # Row AU
                VCCO_705[0]: landpattern.AU[20],
                # Row AV
                VCCO_705[1]: landpattern.AV[20],
                # Row BF
                IO_L0N_H0O0P1_706: landpattern.BF[18],
                # Row BE
                IO_L0P_H0O0P0_706: landpattern.BE[18],
                # Row BA
                IO_L10N_H0O2P5_706: landpattern.BA[17],
                # Row AY
                IO_L10P_H0O2P4_706: landpattern.AY[17],
                IO_L11N_H0O2P7_706: landpattern.AY[18],
                # Row AW
                IO_L11P_H0O2P6_706: landpattern.AW[18],
                IO_L12N_H0O3P1_706: landpattern.AW[16],
                IO_L12P_H0O3P0_706: landpattern.AW[15],
                # Row AU
                IO_L13N_XCC_H0O3P3_706: landpattern.AU[18],
                # Row AT
                IO_L13P_XCC_H0O3P2_706: landpattern.AT[19],
                # Row AU
                IO_L14N_H0O3P5_706: landpattern.AU[17],
                # Row AT
                IO_L14P_H0O3P4_706: landpattern.AT[16],
                # Row AU
                IO_L15N_H0O3P7_706: landpattern.AU[15],
                # Row AT
                IO_L15P_H0O3P6_706: landpattern.AT[15],
                # Row BF
                IO_L1N_XCC_H0O0P3_706: landpattern.BF[16],
                IO_L1P_XCC_H0O0P2_706: landpattern.BF[15],
                # Row BE
                IO_L2N_H0O0P5_706: landpattern.BE[15],
                # Row BD
                IO_L2P_H0O0P4_706: landpattern.BD[16],
                # Row BC
                IO_L3N_GC_H0O0P7_706: landpattern.BC[15],
                IO_L3P_GC_H0O0P6_706: landpattern.BC[14],
                # Row BD
                IO_L4N_H0O1P1_706: landpattern.BD[17],
                # Row BC
                IO_L4P_H0O1P0_706: landpattern.BC[17],
                # Row BF
                IO_L5N_XCC_H0O1P3_706: landpattern.BF[17],
                # Row BE
                IO_L5P_XCC_H0O1P2_706: landpattern.BE[16],
                # Row BB
                IO_L6N_H0O1P5_706: landpattern.BB[19],
                # Row BA
                IO_L6P_H0O1P4_706: landpattern.BA[19],
                # Row BC
                IO_L7N_H0O1P7_706: landpattern.BC[18],
                # Row BB
                IO_L7P_H0O1P6_706: landpattern.BB[18],
                IO_L8N_H0O2P1_706: landpattern.BB[16],
                IO_L8P_H0O2P0_706: landpattern.BB[15],
                # Row BA
                IO_L9N_XCC_H0O2P3_706: landpattern.BA[16],
                # Row AY
                IO_L9P_XCC_H0O2P2_706: landpattern.AY[15],
                # Row AV
                VCCO_706[0]: landpattern.AV[22],
                # Row AW
                VCCO_706[1]: landpattern.AW[22],
                # Row AU
                IO_L16N_H1O0P1_707: landpattern.AU[21],
                # Row AT
                IO_L16P_H1O0P0_707: landpattern.AT[22],
                # Row AY
                IO_L17N_XCC_H1O0P3_707: landpattern.AY[21],
                # Row AW
                IO_L17P_XCC_H1O0P2_707: landpattern.AW[21],
                # Row BA
                IO_L18N_H1O0P5_707: landpattern.BA[20],
                # Row AY
                IO_L18P_H1O0P4_707: landpattern.AY[20],
                # Row BA
                IO_L19N_GC_H1O0P7_707: landpattern.BA[23],
                IO_L19P_GC_H1O0P6_707: landpattern.BA[22],
                # Row BB
                IO_L20N_H1O1P1_707: landpattern.BB[25],
                IO_L20P_H1O1P0_707: landpattern.BB[24],
                IO_L21N_XCC_H1O1P3_707: landpattern.BB[22],
                IO_L21P_XCC_H1O1P2_707: landpattern.BB[21],
                # Row AY
                IO_L22N_H1O1P5_707: landpattern.AY[24],
                IO_L22P_H1O1P4_707: landpattern.AY[23],
                # Row BC
                IO_L23N_H1O1P7_707: landpattern.BC[21],
                IO_L23P_H1O1P6_707: landpattern.BC[20],
                IO_L24N_H1O2P1_707: landpattern.BC[24],
                IO_L24P_H1O2P0_707: landpattern.BC[23],
                # Row BD
                IO_L25N_XCC_H1O2P3_707: landpattern.BD[23],
                IO_L25P_XCC_H1O2P2_707: landpattern.BD[22],
                IO_L26N_H1O2P5_707: landpattern.BD[20],
                IO_L26P_H1O2P4_707: landpattern.BD[19],
                # Row BF
                IO_L27N_H1O2P7_707: landpattern.BF[19],
                # Row BE
                IO_L27P_H1O2P6_707: landpattern.BE[19],
                # Row BF
                IO_L28N_H1O3P1_707: landpattern.BF[21],
                IO_L28P_H1O3P0_707: landpattern.BF[20],
                # Row BE
                IO_L29N_XCC_H1O3P3_707: landpattern.BE[22],
                IO_L29P_XCC_H1O3P2_707: landpattern.BE[21],
                IO_L30N_H1O3P5_707: landpattern.BE[24],
                # Row BD
                IO_L30P_H1O3P4_707: landpattern.BD[25],
                # Row BF
                IO_L31N_H1O3P7_707: landpattern.BF[23],
                IO_L31P_H1O3P6_707: landpattern.BF[22],
                # Row AU
                VCCO_707[0]: landpattern.AU[23],
                # Row AV
                VCCO_707[1]: landpattern.AV[23],
                # Row BF
                IO_L0N_H0O0P1_708: landpattern.BF[26],
                IO_L0P_H0O0P0_708: landpattern.BF[25],
                # Row BA
                IO_L10N_H0O2P5_708: landpattern.BA[28],
                # Row AY
                IO_L10P_H0O2P4_708: landpattern.AY[29],
                IO_L11N_H0O2P7_708: landpattern.AY[27],
                # Row AW
                IO_L11P_H0O2P6_708: landpattern.AW[27],
                # Row AV
                IO_L12N_H0O3P1_708: landpattern.AV[25],
                # Row AU
                IO_L12P_H0O3P0_708: landpattern.AU[24],
                # Row BA
                IO_L13N_XCC_H0O3P3_708: landpattern.BA[25],
                # Row AY
                IO_L13P_XCC_H0O3P2_708: landpattern.AY[26],
                # Row AU
                IO_L14N_H0O3P5_708: landpattern.AU[27],
                # Row AT
                IO_L14P_H0O3P4_708: landpattern.AT[28],
                IO_L15N_H0O3P7_708: landpattern.AT[25],
                IO_L15P_H0O3P6_708: landpattern.AT[24],
                # Row BF
                IO_L1N_XCC_H0O0P3_708: landpattern.BF[27],
                # Row BE
                IO_L1P_XCC_H0O0P2_708: landpattern.BE[27],
                # Row BF
                IO_L2N_H0O0P5_708: landpattern.BF[29],
                IO_L2P_H0O0P4_708: landpattern.BF[28],
                # Row BE
                IO_L3N_GC_H0O0P7_708: landpattern.BE[28],
                # Row BD
                IO_L3P_GC_H0O0P6_708: landpattern.BD[28],
                IO_L4N_H0O1P1_708: landpattern.BD[29],
                # Row BC
                IO_L4P_H0O1P0_708: landpattern.BC[29],
                # Row BF
                IO_L5N_XCC_H0O1P3_708: landpattern.BF[24],
                # Row BE
                IO_L5P_XCC_H0O1P2_708: landpattern.BE[25],
                # Row BD
                IO_L6N_H0O1P5_708: landpattern.BD[26],
                # Row BC
                IO_L6P_H0O1P4_708: landpattern.BC[26],
                IO_L7N_H0O1P7_708: landpattern.BC[27],
                # Row BB
                IO_L7P_H0O1P6_708: landpattern.BB[28],
                IO_L8N_H0O2P1_708: landpattern.BB[27],
                # Row BA
                IO_L8P_H0O2P0_708: landpattern.BA[26],
                # Row AY
                IO_L9N_XCC_H0O2P3_708: landpattern.AY[30],
                # Row AW
                IO_L9P_XCC_H0O2P2_708: landpattern.AW[30],
                VCCO_708[0]: landpattern.AW[24],
                VCCO_708[1]: landpattern.AW[25],
                # Row AU
                IO_L16N_H1O0P1_709: landpattern.AU[30],
                # Row AT
                IO_L16P_H1O0P0_709: landpattern.AT[31],
                IO_L17N_XCC_H1O0P3_709: landpattern.AT[34],
                IO_L17P_XCC_H1O0P2_709: landpattern.AT[33],
                # Row AV
                IO_L18N_H1O0P5_709: landpattern.AV[34],
                # Row AU
                IO_L18P_H1O0P4_709: landpattern.AU[33],
                # Row BA
                IO_L19N_GC_H1O0P7_709: landpattern.BA[32],
                IO_L19P_GC_H1O0P6_709: landpattern.BA[31],
                # Row AY
                IO_L20N_H1O1P1_709: landpattern.AY[33],
                IO_L20P_H1O1P0_709: landpattern.AY[32],
                # Row BD
                IO_L21N_XCC_H1O1P3_709: landpattern.BD[32],
                # Row BC
                IO_L21P_XCC_H1O1P2_709: landpattern.BC[32],
                # Row BB
                IO_L22N_H1O1P5_709: landpattern.BB[30],
                # Row BA
                IO_L22P_H1O1P4_709: landpattern.BA[29],
                # Row BC
                IO_L23N_H1O1P7_709: landpattern.BC[30],
                # Row BB
                IO_L23P_H1O1P6_709: landpattern.BB[31],
                # Row BC
                IO_L24N_H1O2P1_709: landpattern.BC[33],
                # Row BB
                IO_L24P_H1O2P0_709: landpattern.BB[33],
                # Row BF
                IO_L25N_XCC_H1O2P3_709: landpattern.BF[30],
                # Row BE
                IO_L25P_XCC_H1O2P2_709: landpattern.BE[30],
                IO_L26N_H1O2P5_709: landpattern.BE[31],
                # Row BD
                IO_L26P_H1O2P4_709: landpattern.BD[31],
                # Row BF
                IO_L27N_H1O2P7_709: landpattern.BF[35],
                IO_L27P_H1O2P6_709: landpattern.BF[34],
                IO_L28N_H1O3P1_709: landpattern.BF[33],
                # Row BE
                IO_L28P_H1O3P0_709: landpattern.BE[33],
                IO_L29N_XCC_H1O3P3_709: landpattern.BE[34],
                # Row BD
                IO_L29P_XCC_H1O3P2_709: landpattern.BD[34],
                IO_L30N_H1O3P5_709: landpattern.BD[35],
                # Row BC
                IO_L30P_H1O3P4_709: landpattern.BC[35],
                # Row BF
                IO_L31N_H1O3P7_709: landpattern.BF[32],
                IO_L31P_H1O3P6_709: landpattern.BF[31],
                # Row AU
                VCCO_709[0]: landpattern.AU[26],
                # Row AV
                VCCO_709[1]: landpattern.AV[26],
                # Row BE
                IO_L0N_H0O0P1_M2P1_710: landpattern.BE[45],
                # Row BF
                IO_L0P_H0O0P0_M2P0_710: landpattern.BF[44],
                # Row BD
                IO_L10N_H0O2P5_M2P21_710: landpattern.BD[38],
                IO_L10P_H0O2P4_M2P20_710: landpattern.BD[37],
                # Row BF
                IO_L11N_H0O2P7_M2P23_710: landpattern.BF[39],
                IO_L11P_H0O2P6_M2P22_710: landpattern.BF[38],
                # Row BC
                IO_L12N_H0O3P1_M2P25_710: landpattern.BC[38],
                # Row BB
                IO_L12P_H0O3P0_M2P24_710: landpattern.BB[37],
                IO_L13N_XCC_H0O3P3_M2P27_710: landpattern.BB[36],
                # Row BC
                IO_L13P_XCC_H0O3P2_M2P26_710: landpattern.BC[36],
                # Row BF
                IO_L14N_H0O3P5_M2P29_710: landpattern.BF[37],
                IO_L14P_H0O3P4_M2P28_710: landpattern.BF[36],
                # Row BE
                IO_L15N_H0O3P7_M2P31_710: landpattern.BE[37],
                IO_L15P_H0O3P6_M2P30_710: landpattern.BE[36],
                # Row BC
                IO_L1N_XCC_H0O0P3_M2P3_710: landpattern.BC[45],
                # Row BD
                IO_L1P_XCC_H0O0P2_M2P2_710: landpattern.BD[44],
                # Row BC
                IO_L2N_H0O0P5_M2P5_710: landpattern.BC[46],
                # Row BD
                IO_L2P_H0O0P4_M2P4_710: landpattern.BD[46],
                # Row BB
                IO_L3N_GC_H0O0P7_M2P7_710: landpattern.BB[46],
                IO_L3P_GC_H0O0P6_M2P6_710: landpattern.BB[45],
                # Row BC
                IO_L4N_H0O1P1_M2P9_710: landpattern.BC[44],
                # Row BD
                IO_L4P_H0O1P0_M2P8_710: landpattern.BD[43],
                # Row BE
                IO_L5N_XCC_H0O1P3_M2P11_710: landpattern.BE[43],
                # Row BF
                IO_L5P_XCC_H0O1P2_M2P10_710: landpattern.BF[43],
                # Row BD
                IO_L6N_H0O1P5_M2P13_710: landpattern.BD[41],
                IO_L6P_H0O1P4_M2P12_710: landpattern.BD[40],
                # Row BE
                IO_L7N_H0O1P7_M2P15_710: landpattern.BE[42],
                # Row BF
                IO_L7P_H0O1P6_M2P14_710: landpattern.BF[42],
                IO_L8N_H0O2P1_M2P17_710: landpattern.BF[41],
                IO_L8P_H0O2P0_M2P16_710: landpattern.BF[40],
                # Row BE
                IO_L9N_XCC_H0O2P3_M2P19_710: landpattern.BE[40],
                IO_L9P_XCC_H0O2P2_M2P18_710: landpattern.BE[39],
                # Row AV
                VCCO_710[0]: landpattern.AV[28],
                # Row AW
                VCCO_710[1]: landpattern.AW[28],
                # Row BA
                IO_L16N_H1O0P1_M2P33_711: landpattern.BA[34],
                # Row BB
                IO_L16P_H1O0P0_M2P32_711: landpattern.BB[34],
                # Row AY
                IO_L17N_XCC_H1O0P3_M2P35_711: landpattern.AY[35],
                # Row BA
                IO_L17P_XCC_H1O0P2_M2P34_711: landpattern.BA[35],
                IO_L18N_H1O0P5_M2P37_711: landpattern.BA[37],
                # Row AY
                IO_L18P_H1O0P4_M2P36_711: landpattern.AY[36],
                IO_L19N_GC_H1O0P7_M2P39_711: landpattern.AY[38],
                # Row BA
                IO_L19P_GC_H1O0P6_M2P38_711: landpattern.BA[38],
                # Row AW
                IO_L20N_H1O1P1_M2P41_711: landpattern.AW[39],
                # Row AY
                IO_L20P_H1O1P0_M2P40_711: landpattern.AY[39],
                # Row BB
                IO_L21N_XCC_H1O1P3_M2P43_711: landpattern.BB[39],
                # Row BC
                IO_L21P_XCC_H1O1P2_M2P42_711: landpattern.BC[39],
                # Row AY
                IO_L22N_H1O1P5_M2P45_711: landpattern.AY[41],
                # Row AW
                IO_L22P_H1O1P4_M2P44_711: landpattern.AW[40],
                # Row BA
                IO_L23N_H1O1P7_M2P47_711: landpattern.BA[40],
                # Row BB
                IO_L23P_H1O1P6_M2P46_711: landpattern.BB[40],
                # Row BA
                IO_L24N_H1O2P1_M2P49_711: landpattern.BA[43],
                # Row BB
                IO_L24P_H1O2P0_M2P48_711: landpattern.BB[42],
                # Row AY
                IO_L25N_XCC_H1O2P3_M2P51_711: landpattern.AY[42],
                # Row BA
                IO_L25P_XCC_H1O2P2_M2P50_711: landpattern.BA[41],
                # Row AW
                IO_L26N_H1O2P5_M2P53_711: landpattern.AW[43],
                IO_L26P_H1O2P4_M2P52_711: landpattern.AW[42],
                IO_L27N_H1O2P7_M2P55_711: landpattern.AW[46],
                # Row AY
                IO_L27P_H1O2P6_M2P54_711: landpattern.AY[45],
                # Row AW
                IO_L28N_H1O3P1_M2P57_711: landpattern.AW[45],
                # Row AY
                IO_L28P_H1O3P0_M2P56_711: landpattern.AY[44],
                # Row BA
                IO_L29N_XCC_H1O3P3_M2P59_711: landpattern.BA[44],
                # Row BB
                IO_L29P_XCC_H1O3P2_M2P58_711: landpattern.BB[43],
                # Row AY
                IO_L30N_H1O3P5_M2P61_711: landpattern.AY[46],
                # Row BA
                IO_L30P_H1O3P4_M2P60_711: landpattern.BA[46],
                # Row BC
                IO_L31N_H1O3P7_M2P63_711: landpattern.BC[42],
                IO_L31P_H1O3P6_M2P62_711: landpattern.BC[41],
                # Row AU
                VCCO_711[0]: landpattern.AU[29],
                # Row AV
                VCCO_711[1]: landpattern.AV[29],
                # Row AU
                IO_L0N_H0O0P1_M2P65_712: landpattern.AU[45],
                IO_L0P_H0O0P0_M2P64_712: landpattern.AU[44],
                # Row AT
                IO_L10N_H0O2P5_M2P85_712: landpattern.AT[39],
                # Row AR
                IO_L10P_H0O2P4_M2P84_712: landpattern.AR[38],
                # Row AU
                IO_L11N_H0O2P7_M2P87_712: landpattern.AU[39],
                IO_L11P_H0O2P6_M2P86_712: landpattern.AU[38],
                # Row AV
                IO_L12N_H0O3P1_M2P89_712: landpattern.AV[38],
                IO_L12P_H0O3P0_M2P88_712: landpattern.AV[37],
                # Row AR
                IO_L13N_XCC_H0O3P3_M2P91_712: landpattern.AR[37],
                # Row AT
                IO_L13P_XCC_H0O3P2_M2P90_712: landpattern.AT[37],
                IO_L14N_H0O3P5_M2P93_712: landpattern.AT[36],
                # Row AU
                IO_L14P_H0O3P4_M2P92_712: landpattern.AU[36],
                # Row AW
                IO_L15N_H0O3P7_M2P95_712: landpattern.AW[37],
                IO_L15P_H0O3P6_M2P94_712: landpattern.AW[36],
                # Row AT
                IO_L1N_XCC_H0O0P3_M2P67_712: landpattern.AT[45],
                # Row AR
                IO_L1P_XCC_H0O0P2_M2P66_712: landpattern.AR[44],
                IO_L2N_H0O0P5_M2P69_712: landpattern.AR[46],
                # Row AT
                IO_L2P_H0O0P4_M2P68_712: landpattern.AT[46],
                # Row AU
                IO_L3N_GC_H0O0P7_M2P71_712: landpattern.AU[46],
                # Row AV
                IO_L3P_GC_H0O0P6_M2P70_712: landpattern.AV[46],
                # Row AR
                IO_L4N_H0O1P1_M2P73_712: landpattern.AR[43],
                # Row AT
                IO_L4P_H0O1P0_M2P72_712: landpattern.AT[43],
                # Row AV
                IO_L5N_XCC_H0O1P3_M2P75_712: landpattern.AV[44],
                IO_L5P_XCC_H0O1P2_M2P74_712: landpattern.AV[43],
                # Row AR
                IO_L6N_H0O1P5_M2P77_712: landpattern.AR[40],
                # Row AT
                IO_L6P_H0O1P4_M2P76_712: landpattern.AT[40],
                # Row AV
                IO_L7N_H0O1P7_M2P79_712: landpattern.AV[41],
                IO_L7P_H0O1P6_M2P78_712: landpattern.AV[40],
                # Row AU
                IO_L8N_H0O2P1_M2P81_712: landpattern.AU[42],
                IO_L8P_H0O2P0_M2P80_712: landpattern.AU[41],
                # Row AT
                IO_L9N_XCC_H0O2P3_M2P83_712: landpattern.AT[42],
                # Row AR
                IO_L9P_XCC_H0O2P2_M2P82_712: landpattern.AR[41],
                # Row AV
                VCCO_712[0]: landpattern.AV[31],
                # Row AW
                VCCO_712[1]: landpattern.AW[31],
                # Row AP
                IO_L16N_H1O0P1_M3P97_713: landpattern.AP[36],
                # Row AR
                IO_L16P_H1O0P0_M3P96_713: landpattern.AR[35],
                # Row AM
                IO_L17N_XCC_H1O0P3_M3P99_713: landpattern.AM[37],
                # Row AL
                IO_L17P_XCC_H1O0P2_M3P98_713: landpattern.AL[36],
                # Row AN
                IO_L18N_H1O0P5_M3P101_713: landpattern.AN[37],
                IO_L18P_H1O0P4_M3P100_713: landpattern.AN[36],
                # Row AP
                IO_L19N_GC_H1O0P7_M3P103_713: landpattern.AP[39],
                IO_L19P_GC_H1O0P6_M3P102_713: landpattern.AP[38],
                # Row AL
                IO_L20N_H1O1P1_M3P105_713: landpattern.AL[38],
                # Row AM
                IO_L20P_H1O1P0_M3P104_713: landpattern.AM[38],
                IO_L21N_XCC_H1O1P3_M3P107_713: landpattern.AM[40],
                # Row AL
                IO_L21P_XCC_H1O1P2_M3P106_713: landpattern.AL[39],
                # Row AN
                IO_L22N_H1O1P5_M3P109_713: landpattern.AN[40],
                IO_L22P_H1O1P4_M3P108_713: landpattern.AN[39],
                # Row AP
                IO_L23N_H1O1P7_M3P111_713: landpattern.AP[42],
                IO_L23P_H1O1P6_M3P110_713: landpattern.AP[41],
                # Row AL
                IO_L24N_H1O2P1_M3P113_713: landpattern.AL[41],
                # Row AM
                IO_L24P_H1O2P0_M3P112_713: landpattern.AM[41],
                IO_L25N_XCC_H1O2P3_M3P115_713: landpattern.AM[43],
                # Row AL
                IO_L25P_XCC_H1O2P2_M3P114_713: landpattern.AL[42],
                # Row AN
                IO_L26N_H1O2P5_M3P117_713: landpattern.AN[43],
                IO_L26P_H1O2P4_M3P116_713: landpattern.AN[42],
                # Row AP
                IO_L27N_H1O2P7_M3P119_713: landpattern.AP[45],
                IO_L27P_H1O2P6_M3P118_713: landpattern.AP[44],
                # Row AL
                IO_L28N_H1O3P1_M3P121_713: landpattern.AL[44],
                # Row AM
                IO_L28P_H1O3P0_M3P120_713: landpattern.AM[44],
                # Row AL
                IO_L29N_XCC_H1O3P3_M3P123_713: landpattern.AL[46],
                IO_L29P_XCC_H1O3P2_M3P122_713: landpattern.AL[45],
                # Row AM
                IO_L30N_H1O3P5_M3P125_713: landpattern.AM[46],
                # Row AN
                IO_L30P_H1O3P4_M3P124_713: landpattern.AN[45],
                IO_L31N_H1O3P7_M3P127_713: landpattern.AN[46],
                # Row AP
                IO_L31P_H1O3P6_M3P126_713: landpattern.AP[46],
                # Row AU
                VCCO_713[0]: landpattern.AU[32],
                # Row AV
                VCCO_713[1]: landpattern.AV[32],
                # Row AK
                IO_L0N_H0O0P1_M3P129_714: landpattern.AK[46],
                IO_L0P_H0O0P0_M3P128_714: landpattern.AK[45],
                # Row AG
                IO_L10N_H0O2P5_M3P149_714: landpattern.AG[40],
                IO_L10P_H0O2P4_M3P148_714: landpattern.AG[39],
                # Row AH
                IO_L11N_H0O2P7_M3P151_714: landpattern.AH[39],
                IO_L11P_H0O2P6_M3P150_714: landpattern.AH[38],
                # Row AJ
                IO_L12N_H0O3P1_M3P153_714: landpattern.AJ[38],
                IO_L12P_H0O3P0_M3P152_714: landpattern.AJ[37],
                # Row AF
                IO_L13N_XCC_H0O3P3_M3P155_714: landpattern.AF[37],
                # Row AG
                IO_L13P_XCC_H0O3P2_M3P154_714: landpattern.AG[37],
                IO_L14N_H0O3P5_M3P157_714: landpattern.AG[36],
                # Row AH
                IO_L14P_H0O3P4_M3P156_714: landpattern.AH[36],
                # Row AK
                IO_L15N_H0O3P7_M3P159_714: landpattern.AK[37],
                IO_L15P_H0O3P6_M3P158_714: landpattern.AK[36],
                # Row AH
                IO_L1N_XCC_H0O0P3_M3P131_714: landpattern.AH[46],
                # Row AJ
                IO_L1P_XCC_H0O0P2_M3P130_714: landpattern.AJ[46],
                # Row AG
                IO_L2N_H0O0P5_M3P133_714: landpattern.AG[46],
                IO_L2P_H0O0P4_M3P132_714: landpattern.AG[45],
                # Row AH
                IO_L3N_GC_H0O0P7_M3P135_714: landpattern.AH[45],
                IO_L3P_GC_H0O0P6_M3P134_714: landpattern.AH[44],
                # Row AJ
                IO_L4N_H0O1P1_M3P137_714: landpattern.AJ[44],
                IO_L4P_H0O1P0_M3P136_714: landpattern.AJ[43],
                # Row AK
                IO_L5N_XCC_H0O1P3_M3P139_714: landpattern.AK[43],
                IO_L5P_XCC_H0O1P2_M3P138_714: landpattern.AK[42],
                # Row AG
                IO_L6N_H0O1P5_M3P141_714: landpattern.AG[43],
                IO_L6P_H0O1P4_M3P140_714: landpattern.AG[42],
                # Row AH
                IO_L7N_H0O1P7_M3P143_714: landpattern.AH[42],
                IO_L7P_H0O1P6_M3P142_714: landpattern.AH[41],
                # Row AJ
                IO_L8N_H0O2P1_M3P145_714: landpattern.AJ[41],
                IO_L8P_H0O2P0_M3P144_714: landpattern.AJ[40],
                # Row AK
                IO_L9N_XCC_H0O2P3_M3P147_714: landpattern.AK[40],
                IO_L9P_XCC_H0O2P2_M3P146_714: landpattern.AK[39],
                # Row AW
                VCCO_714[0]: landpattern.AW[33],
                VCCO_714[1]: landpattern.AW[34],
                # Row AD
                IO_L16N_H1O0P1_M3P161_715: landpattern.AD[36],
                # Row AE
                IO_L16P_H1O0P0_M3P160_715: landpattern.AE[36],
                # Row AC
                IO_L17N_XCC_H1O0P3_M3P163_715: landpattern.AC[37],
                # Row AD
                IO_L17P_XCC_H1O0P2_M3P162_715: landpattern.AD[37],
                # Row AE
                IO_L18N_H1O0P5_M3P165_715: landpattern.AE[38],
                # Row AF
                IO_L18P_H1O0P4_M3P164_715: landpattern.AF[38],
                # Row AD
                IO_L19N_GC_H1O0P7_M3P167_715: landpattern.AD[39],
                # Row AE
                IO_L19P_GC_H1O0P6_M3P166_715: landpattern.AE[39],
                # Row AB
                IO_L20N_H1O1P1_M3P169_715: landpattern.AB[38],
                # Row AC
                IO_L20P_H1O1P0_M3P168_715: landpattern.AC[38],
                IO_L21N_XCC_H1O1P3_M3P171_715: landpattern.AC[40],
                # Row AD
                IO_L21P_XCC_H1O1P2_M3P170_715: landpattern.AD[40],
                # Row AF
                IO_L22N_H1O1P5_M3P173_715: landpattern.AF[41],
                IO_L22P_H1O1P4_M3P172_715: landpattern.AF[40],
                # Row AE
                IO_L23N_H1O1P7_M3P175_715: landpattern.AE[42],
                IO_L23P_H1O1P6_M3P174_715: landpattern.AE[41],
                # Row AB
                IO_L24N_H1O2P1_M3P177_715: landpattern.AB[41],
                # Row AC
                IO_L24P_H1O2P0_M3P176_715: landpattern.AC[41],
                # Row AF
                IO_L25N_XCC_H1O2P3_M3P179_715: landpattern.AF[44],
                IO_L25P_XCC_H1O2P2_M3P178_715: landpattern.AF[43],
                # Row AD
                IO_L26N_H1O2P5_M3P181_715: landpattern.AD[43],
                IO_L26P_H1O2P4_M3P180_715: landpattern.AD[42],
                # Row AC
                IO_L27N_H1O2P7_M3P183_715: landpattern.AC[44],
                IO_L27P_H1O2P6_M3P182_715: landpattern.AC[43],
                # Row AE
                IO_L28N_H1O3P1_M3P185_715: landpattern.AE[45],
                IO_L28P_H1O3P0_M3P184_715: landpattern.AE[44],
                # Row AD
                IO_L29N_XCC_H1O3P3_M3P187_715: landpattern.AD[46],
                IO_L29P_XCC_H1O3P2_M3P186_715: landpattern.AD[45],
                # Row AB
                IO_L30N_H1O3P5_M3P189_715: landpattern.AB[46],
                # Row AC
                IO_L30P_H1O3P4_M3P188_715: landpattern.AC[46],
                # Row AE
                IO_L31N_H1O3P7_M3P191_715: landpattern.AE[46],
                # Row AF
                IO_L31P_H1O3P6_M3P190_715: landpattern.AF[46],
                # Row AU
                VCCO_715[0]: landpattern.AU[35],
                # Row AV
                VCCO_715[1]: landpattern.AV[35],
                # Row A
                GND[0]: landpattern.A[10],
                GND[1]: landpattern.A[12],
                GND[2]: landpattern.A[14],
                GND[3]: landpattern.A[16],
                GND[4]: landpattern.A[18],
                GND[5]: landpattern.A[2],
                GND[6]: landpattern.A[20],
                GND[7]: landpattern.A[22],
                GND[8]: landpattern.A[24],
                GND[9]: landpattern.A[29],
                GND[10]: landpattern.A[3],
                GND[11]: landpattern.A[31],
                GND[12]: landpattern.A[33],
                GND[13]: landpattern.A[35],
                GND[14]: landpattern.A[37],
                GND[15]: landpattern.A[39],
                GND[16]: landpattern.A[4],
                GND[17]: landpattern.A[41],
                GND[18]: landpattern.A[43],
                GND[19]: landpattern.A[45],
                GND[20]: landpattern.A[5],
                GND[21]: landpattern.A[6],
                GND[22]: landpattern.A[8],
                # Row AA
                GND[23]: landpattern.AA[11],
                GND[24]: landpattern.AA[13],
                GND[25]: landpattern.AA[15],
                GND[26]: landpattern.AA[17],
                GND[27]: landpattern.AA[21],
                GND[28]: landpattern.AA[23],
                GND[29]: landpattern.AA[25],
                GND[30]: landpattern.AA[27],
                GND[31]: landpattern.AA[29],
                GND[32]: landpattern.AA[3],
                GND[33]: landpattern.AA[33],
                GND[34]: landpattern.AA[37],
                GND[35]: landpattern.AA[38],
                GND[36]: landpattern.AA[4],
                GND[37]: landpattern.AA[41],
                GND[38]: landpattern.AA[46],
                GND[39]: landpattern.AA[5],
                GND[40]: landpattern.AA[8],
                # Row AB
                GND[41]: landpattern.AB[1],
                GND[42]: landpattern.AB[10],
                GND[43]: landpattern.AB[11],
                GND[44]: landpattern.AB[13],
                GND[45]: landpattern.AB[16],
                GND[46]: landpattern.AB[19],
                GND[47]: landpattern.AB[2],
                GND[48]: landpattern.AB[22],
                GND[49]: landpattern.AB[24],
                GND[50]: landpattern.AB[26],
                GND[51]: landpattern.AB[28],
                GND[52]: landpattern.AB[3],
                GND[53]: landpattern.AB[31],
                GND[54]: landpattern.AB[33],
                GND[55]: landpattern.AB[34],
                GND[56]: landpattern.AB[35],
                GND[57]: landpattern.AB[36],
                GND[58]: landpattern.AB[37],
                GND[59]: landpattern.AB[39],
                GND[60]: landpattern.AB[40],
                GND[61]: landpattern.AB[42],
                GND[62]: landpattern.AB[43],
                GND[63]: landpattern.AB[44],
                GND[64]: landpattern.AB[45],
                GND[65]: landpattern.AB[6],
                GND[66]: landpattern.AB[7],
                GND[67]: landpattern.AB[8],
                GND[68]: landpattern.AB[9],
                # Row AC
                GND[69]: landpattern.AC[12],
                GND[70]: landpattern.AC[15],
                GND[71]: landpattern.AC[18],
                GND[72]: landpattern.AC[21],
                GND[73]: landpattern.AC[23],
                GND[74]: landpattern.AC[25],
                GND[75]: landpattern.AC[27],
                GND[76]: landpattern.AC[29],
                GND[77]: landpattern.AC[3],
                GND[78]: landpattern.AC[30],
                GND[79]: landpattern.AC[33],
                GND[80]: landpattern.AC[36],
                GND[81]: landpattern.AC[39],
                GND[82]: landpattern.AC[4],
                GND[83]: landpattern.AC[42],
                GND[84]: landpattern.AC[45],
                GND[85]: landpattern.AC[5],
                GND[86]: landpattern.AC[6],
                GND[87]: landpattern.AC[9],
                # Row AD
                GND[88]: landpattern.AD[11],
                GND[89]: landpattern.AD[14],
                GND[90]: landpattern.AD[17],
                GND[91]: landpattern.AD[2],
                GND[92]: landpattern.AD[20],
                GND[93]: landpattern.AD[24],
                GND[94]: landpattern.AD[26],
                GND[95]: landpattern.AD[28],
                GND[96]: landpattern.AD[32],
                GND[97]: landpattern.AD[35],
                GND[98]: landpattern.AD[38],
                GND[99]: landpattern.AD[41],
                GND[100]: landpattern.AD[44],
                GND[101]: landpattern.AD[5],
                GND[102]: landpattern.AD[8],
                # Row AE
                GND[103]: landpattern.AE[10],
                GND[104]: landpattern.AE[13],
                GND[105]: landpattern.AE[16],
                GND[106]: landpattern.AE[22],
                GND[107]: landpattern.AE[23],
                GND[108]: landpattern.AE[25],
                GND[109]: landpattern.AE[27],
                GND[110]: landpattern.AE[29],
                GND[111]: landpattern.AE[31],
                GND[112]: landpattern.AE[34],
                GND[113]: landpattern.AE[37],
                GND[114]: landpattern.AE[4],
                GND[115]: landpattern.AE[40],
                GND[116]: landpattern.AE[43],
                GND[117]: landpattern.AE[7],
                # Row AF
                GND[118]: landpattern.AF[12],
                GND[119]: landpattern.AF[15],
                GND[120]: landpattern.AF[18],
                GND[121]: landpattern.AF[21],
                GND[122]: landpattern.AF[26],
                GND[123]: landpattern.AF[28],
                GND[124]: landpattern.AF[3],
                GND[125]: landpattern.AF[30],
                GND[126]: landpattern.AF[33],
                GND[127]: landpattern.AF[36],
                GND[128]: landpattern.AF[39],
                GND[129]: landpattern.AF[42],
                GND[130]: landpattern.AF[45],
                GND[131]: landpattern.AF[6],
                GND[132]: landpattern.AF[9],
                # Row AG
                GND[133]: landpattern.AG[11],
                GND[134]: landpattern.AG[14],
                GND[135]: landpattern.AG[17],
                GND[136]: landpattern.AG[2],
                GND[137]: landpattern.AG[20],
                GND[138]: landpattern.AG[25],
                GND[139]: landpattern.AG[27],
                GND[140]: landpattern.AG[29],
                GND[141]: landpattern.AG[32],
                GND[142]: landpattern.AG[35],
                GND[143]: landpattern.AG[38],
                GND[144]: landpattern.AG[41],
                GND[145]: landpattern.AG[44],
                GND[146]: landpattern.AG[5],
                GND[147]: landpattern.AG[8],
                # Row AH
                GND[148]: landpattern.AH[10],
                GND[149]: landpattern.AH[13],
                GND[150]: landpattern.AH[16],
                GND[151]: landpattern.AH[19],
                GND[152]: landpattern.AH[22],
                GND[153]: landpattern.AH[26],
                GND[154]: landpattern.AH[28],
                GND[155]: landpattern.AH[31],
                GND[156]: landpattern.AH[34],
                GND[157]: landpattern.AH[37],
                GND[158]: landpattern.AH[4],
                GND[159]: landpattern.AH[40],
                GND[160]: landpattern.AH[43],
                GND[161]: landpattern.AH[7],
                # Row AJ
                GND[162]: landpattern.AJ[12],
                GND[163]: landpattern.AJ[15],
                GND[164]: landpattern.AJ[18],
                GND[165]: landpattern.AJ[21],
                GND[166]: landpattern.AJ[25],
                GND[167]: landpattern.AJ[27],
                GND[168]: landpattern.AJ[29],
                GND[169]: landpattern.AJ[3],
                GND[170]: landpattern.AJ[30],
                GND[171]: landpattern.AJ[33],
                GND[172]: landpattern.AJ[36],
                GND[173]: landpattern.AJ[39],
                GND[174]: landpattern.AJ[42],
                GND[175]: landpattern.AJ[45],
                GND[176]: landpattern.AJ[6],
                GND[177]: landpattern.AJ[9],
                # Row AK
                GND[178]: landpattern.AK[11],
                GND[179]: landpattern.AK[14],
                GND[180]: landpattern.AK[17],
                GND[181]: landpattern.AK[2],
                GND[182]: landpattern.AK[20],
                GND[183]: landpattern.AK[24],
                GND[184]: landpattern.AK[26],
                GND[185]: landpattern.AK[28],
                GND[186]: landpattern.AK[32],
                GND[187]: landpattern.AK[35],
                GND[188]: landpattern.AK[38],
                GND[189]: landpattern.AK[41],
                GND[190]: landpattern.AK[44],
                GND[191]: landpattern.AK[5],
                GND[192]: landpattern.AK[8],
                # Row AL
                GND[193]: landpattern.AL[10],
                GND[194]: landpattern.AL[13],
                GND[195]: landpattern.AL[16],
                GND[196]: landpattern.AL[19],
                GND[197]: landpattern.AL[22],
                GND[198]: landpattern.AL[25],
                GND[199]: landpattern.AL[28],
                GND[200]: landpattern.AL[31],
                GND[201]: landpattern.AL[34],
                GND[202]: landpattern.AL[37],
                GND[203]: landpattern.AL[4],
                GND[204]: landpattern.AL[40],
                GND[205]: landpattern.AL[43],
                GND[206]: landpattern.AL[7],
                # Row AM
                GND[207]: landpattern.AM[12],
                GND[208]: landpattern.AM[15],
                GND[209]: landpattern.AM[18],
                GND[210]: landpattern.AM[21],
                GND[211]: landpattern.AM[24],
                GND[212]: landpattern.AM[27],
                GND[213]: landpattern.AM[3],
                GND[214]: landpattern.AM[30],
                GND[215]: landpattern.AM[36],
                GND[216]: landpattern.AM[39],
                GND[217]: landpattern.AM[42],
                GND[218]: landpattern.AM[45],
                GND[219]: landpattern.AM[6],
                GND[220]: landpattern.AM[9],
                # Row AN
                GND[221]: landpattern.AN[11],
                GND[222]: landpattern.AN[14],
                GND[223]: landpattern.AN[17],
                GND[224]: landpattern.AN[2],
                GND[225]: landpattern.AN[20],
                GND[226]: landpattern.AN[23],
                GND[227]: landpattern.AN[26],
                GND[228]: landpattern.AN[29],
                GND[229]: landpattern.AN[32],
                GND[230]: landpattern.AN[35],
                GND[231]: landpattern.AN[38],
                GND[232]: landpattern.AN[41],
                GND[233]: landpattern.AN[44],
                GND[234]: landpattern.AN[5],
                GND[235]: landpattern.AN[8],
                # Row AP
                GND[236]: landpattern.AP[10],
                GND[237]: landpattern.AP[13],
                GND[238]: landpattern.AP[16],
                GND[239]: landpattern.AP[19],
                GND[240]: landpattern.AP[22],
                GND[241]: landpattern.AP[25],
                GND[242]: landpattern.AP[28],
                GND[243]: landpattern.AP[31],
                GND[244]: landpattern.AP[34],
                GND[245]: landpattern.AP[37],
                GND[246]: landpattern.AP[4],
                GND[247]: landpattern.AP[40],
                GND[248]: landpattern.AP[43],
                GND[249]: landpattern.AP[7],
                # Row AR
                GND[250]: landpattern.AR[12],
                GND[251]: landpattern.AR[15],
                GND[252]: landpattern.AR[18],
                GND[253]: landpattern.AR[21],
                GND[254]: landpattern.AR[24],
                GND[255]: landpattern.AR[27],
                GND[256]: landpattern.AR[3],
                GND[257]: landpattern.AR[30],
                GND[258]: landpattern.AR[33],
                GND[259]: landpattern.AR[36],
                GND[260]: landpattern.AR[39],
                GND[261]: landpattern.AR[42],
                GND[262]: landpattern.AR[45],
                GND[263]: landpattern.AR[6],
                GND[264]: landpattern.AR[9],
                # Row AT
                GND[265]: landpattern.AT[11],
                GND[266]: landpattern.AT[14],
                GND[267]: landpattern.AT[17],
                GND[268]: landpattern.AT[2],
                GND[269]: landpattern.AT[20],
                GND[270]: landpattern.AT[23],
                GND[271]: landpattern.AT[26],
                GND[272]: landpattern.AT[29],
                GND[273]: landpattern.AT[32],
                GND[274]: landpattern.AT[35],
                GND[275]: landpattern.AT[38],
                GND[276]: landpattern.AT[41],
                GND[277]: landpattern.AT[44],
                GND[278]: landpattern.AT[5],
                GND[279]: landpattern.AT[8],
                # Row AU
                GND[280]: landpattern.AU[10],
                GND[281]: landpattern.AU[13],
                GND[282]: landpattern.AU[16],
                GND[283]: landpattern.AU[19],
                GND[284]: landpattern.AU[22],
                GND[285]: landpattern.AU[25],
                GND[286]: landpattern.AU[28],
                GND[287]: landpattern.AU[31],
                GND[288]: landpattern.AU[34],
                GND[289]: landpattern.AU[37],
                GND[290]: landpattern.AU[4],
                GND[291]: landpattern.AU[40],
                GND[292]: landpattern.AU[43],
                GND[293]: landpattern.AU[7],
                # Row AV
                GND[294]: landpattern.AV[12],
                GND[295]: landpattern.AV[15],
                GND[296]: landpattern.AV[18],
                GND[297]: landpattern.AV[21],
                GND[298]: landpattern.AV[24],
                GND[299]: landpattern.AV[27],
                GND[300]: landpattern.AV[3],
                GND[301]: landpattern.AV[30],
                GND[302]: landpattern.AV[33],
                GND[303]: landpattern.AV[36],
                GND[304]: landpattern.AV[39],
                GND[305]: landpattern.AV[42],
                GND[306]: landpattern.AV[45],
                GND[307]: landpattern.AV[6],
                GND[308]: landpattern.AV[9],
                # Row AW
                GND[309]: landpattern.AW[11],
                GND[310]: landpattern.AW[14],
                GND[311]: landpattern.AW[17],
                GND[312]: landpattern.AW[2],
                GND[313]: landpattern.AW[20],
                GND[314]: landpattern.AW[23],
                GND[315]: landpattern.AW[26],
                GND[316]: landpattern.AW[29],
                GND[317]: landpattern.AW[32],
                GND[318]: landpattern.AW[35],
                GND[319]: landpattern.AW[38],
                GND[320]: landpattern.AW[41],
                GND[321]: landpattern.AW[44],
                GND[322]: landpattern.AW[5],
                GND[323]: landpattern.AW[8],
                # Row AY
                GND[324]: landpattern.AY[10],
                GND[325]: landpattern.AY[13],
                GND[326]: landpattern.AY[16],
                GND[327]: landpattern.AY[19],
                GND[328]: landpattern.AY[22],
                GND[329]: landpattern.AY[25],
                GND[330]: landpattern.AY[28],
                GND[331]: landpattern.AY[31],
                GND[332]: landpattern.AY[34],
                GND[333]: landpattern.AY[37],
                GND[334]: landpattern.AY[4],
                GND[335]: landpattern.AY[40],
                GND[336]: landpattern.AY[43],
                GND[337]: landpattern.AY[7],
                # Row B
                GND[338]: landpattern.B[1],
                GND[339]: landpattern.B[10],
                GND[340]: landpattern.B[12],
                GND[341]: landpattern.B[14],
                GND[342]: landpattern.B[16],
                GND[343]: landpattern.B[18],
                GND[344]: landpattern.B[2],
                GND[345]: landpattern.B[20],
                GND[346]: landpattern.B[22],
                GND[347]: landpattern.B[26],
                GND[348]: landpattern.B[29],
                GND[349]: landpattern.B[3],
                GND[350]: landpattern.B[31],
                GND[351]: landpattern.B[33],
                GND[352]: landpattern.B[35],
                GND[353]: landpattern.B[37],
                GND[354]: landpattern.B[39],
                GND[355]: landpattern.B[41],
                GND[356]: landpattern.B[43],
                GND[357]: landpattern.B[45],
                GND[358]: landpattern.B[46],
                GND[359]: landpattern.B[6],
                GND[360]: landpattern.B[8],
                # Row BA
                GND[361]: landpattern.BA[12],
                GND[362]: landpattern.BA[15],
                GND[363]: landpattern.BA[18],
                GND[364]: landpattern.BA[21],
                GND[365]: landpattern.BA[24],
                GND[366]: landpattern.BA[27],
                GND[367]: landpattern.BA[3],
                GND[368]: landpattern.BA[30],
                GND[369]: landpattern.BA[33],
                GND[370]: landpattern.BA[36],
                GND[371]: landpattern.BA[39],
                GND[372]: landpattern.BA[42],
                GND[373]: landpattern.BA[45],
                GND[374]: landpattern.BA[6],
                GND[375]: landpattern.BA[9],
                # Row BB
                GND[376]: landpattern.BB[11],
                GND[377]: landpattern.BB[14],
                GND[378]: landpattern.BB[17],
                GND[379]: landpattern.BB[2],
                GND[380]: landpattern.BB[20],
                GND[381]: landpattern.BB[23],
                GND[382]: landpattern.BB[26],
                GND[383]: landpattern.BB[29],
                GND[384]: landpattern.BB[32],
                GND[385]: landpattern.BB[35],
                GND[386]: landpattern.BB[38],
                GND[387]: landpattern.BB[41],
                GND[388]: landpattern.BB[44],
                GND[389]: landpattern.BB[5],
                GND[390]: landpattern.BB[8],
                # Row BC
                GND[391]: landpattern.BC[10],
                GND[392]: landpattern.BC[13],
                GND[393]: landpattern.BC[16],
                GND[394]: landpattern.BC[19],
                GND[395]: landpattern.BC[22],
                GND[396]: landpattern.BC[25],
                GND[397]: landpattern.BC[28],
                GND[398]: landpattern.BC[31],
                GND[399]: landpattern.BC[34],
                GND[400]: landpattern.BC[37],
                GND[401]: landpattern.BC[4],
                GND[402]: landpattern.BC[40],
                GND[403]: landpattern.BC[43],
                GND[404]: landpattern.BC[7],
                # Row BD
                GND[405]: landpattern.BD[12],
                GND[406]: landpattern.BD[15],
                GND[407]: landpattern.BD[18],
                GND[408]: landpattern.BD[21],
                GND[409]: landpattern.BD[24],
                GND[410]: landpattern.BD[27],
                GND[411]: landpattern.BD[3],
                GND[412]: landpattern.BD[30],
                GND[413]: landpattern.BD[33],
                GND[414]: landpattern.BD[36],
                GND[415]: landpattern.BD[39],
                GND[416]: landpattern.BD[42],
                GND[417]: landpattern.BD[45],
                GND[418]: landpattern.BD[6],
                GND[419]: landpattern.BD[9],
                # Row BE
                GND[420]: landpattern.BE[1],
                GND[421]: landpattern.BE[11],
                GND[422]: landpattern.BE[14],
                GND[423]: landpattern.BE[17],
                GND[424]: landpattern.BE[2],
                GND[425]: landpattern.BE[20],
                GND[426]: landpattern.BE[23],
                GND[427]: landpattern.BE[26],
                GND[428]: landpattern.BE[29],
                GND[429]: landpattern.BE[32],
                GND[430]: landpattern.BE[35],
                GND[431]: landpattern.BE[38],
                GND[432]: landpattern.BE[41],
                GND[433]: landpattern.BE[44],
                GND[434]: landpattern.BE[46],
                GND[435]: landpattern.BE[5],
                GND[436]: landpattern.BE[8],
                # Row BF
                GND[437]: landpattern.BF[2],
                GND[438]: landpattern.BF[45],
                # Row C
                GND[439]: landpattern.C[10],
                GND[440]: landpattern.C[11],
                GND[441]: landpattern.C[12],
                GND[442]: landpattern.C[13],
                GND[443]: landpattern.C[14],
                GND[444]: landpattern.C[15],
                GND[445]: landpattern.C[16],
                GND[446]: landpattern.C[17],
                GND[447]: landpattern.C[18],
                GND[448]: landpattern.C[19],
                GND[449]: landpattern.C[20],
                GND[450]: landpattern.C[21],
                GND[451]: landpattern.C[22],
                GND[452]: landpattern.C[23],
                GND[453]: landpattern.C[28],
                GND[454]: landpattern.C[29],
                GND[455]: landpattern.C[3],
                GND[456]: landpattern.C[30],
                GND[457]: landpattern.C[31],
                GND[458]: landpattern.C[32],
                GND[459]: landpattern.C[33],
                GND[460]: landpattern.C[34],
                GND[461]: landpattern.C[35],
                GND[462]: landpattern.C[36],
                GND[463]: landpattern.C[37],
                GND[464]: landpattern.C[38],
                GND[465]: landpattern.C[39],
                GND[466]: landpattern.C[4],
                GND[467]: landpattern.C[40],
                GND[468]: landpattern.C[41],
                GND[469]: landpattern.C[42],
                GND[470]: landpattern.C[43],
                GND[471]: landpattern.C[44],
                GND[472]: landpattern.C[45],
                GND[473]: landpattern.C[46],
                GND[474]: landpattern.C[5],
                GND[475]: landpattern.C[6],
                GND[476]: landpattern.C[7],
                GND[477]: landpattern.C[8],
                GND[478]: landpattern.C[9],
                # Row D
                GND[479]: landpattern.D[1],
                GND[480]: landpattern.D[11],
                GND[481]: landpattern.D[13],
                GND[482]: landpattern.D[15],
                GND[483]: landpattern.D[17],
                GND[484]: landpattern.D[19],
                GND[485]: landpattern.D[2],
                GND[486]: landpattern.D[21],
                GND[487]: landpattern.D[23],
                GND[488]: landpattern.D[25],
                GND[489]: landpattern.D[3],
                GND[490]: landpattern.D[30],
                GND[491]: landpattern.D[32],
                GND[492]: landpattern.D[34],
                GND[493]: landpattern.D[36],
                GND[494]: landpattern.D[38],
                GND[495]: landpattern.D[40],
                GND[496]: landpattern.D[42],
                GND[497]: landpattern.D[44],
                GND[498]: landpattern.D[46],
                GND[499]: landpattern.D[6],
                GND[500]: landpattern.D[7],
                GND[501]: landpattern.D[9],
                # Row E
                GND[502]: landpattern.E[11],
                GND[503]: landpattern.E[13],
                GND[504]: landpattern.E[15],
                GND[505]: landpattern.E[17],
                GND[506]: landpattern.E[19],
                GND[507]: landpattern.E[21],
                GND[508]: landpattern.E[23],
                GND[509]: landpattern.E[27],
                GND[510]: landpattern.E[3],
                GND[511]: landpattern.E[30],
                GND[512]: landpattern.E[32],
                GND[513]: landpattern.E[34],
                GND[514]: landpattern.E[36],
                GND[515]: landpattern.E[38],
                GND[516]: landpattern.E[4],
                GND[517]: landpattern.E[40],
                GND[518]: landpattern.E[42],
                GND[519]: landpattern.E[44],
                GND[520]: landpattern.E[46],
                GND[521]: landpattern.E[5],
                GND[522]: landpattern.E[6],
                GND[523]: landpattern.E[7],
                GND[524]: landpattern.E[9],
                # Row F
                GND[525]: landpattern.F[1],
                GND[526]: landpattern.F[10],
                GND[527]: landpattern.F[11],
                GND[528]: landpattern.F[12],
                GND[529]: landpattern.F[13],
                GND[530]: landpattern.F[14],
                GND[531]: landpattern.F[15],
                GND[532]: landpattern.F[16],
                GND[533]: landpattern.F[17],
                GND[534]: landpattern.F[18],
                GND[535]: landpattern.F[19],
                GND[536]: landpattern.F[2],
                GND[537]: landpattern.F[20],
                GND[538]: landpattern.F[21],
                GND[539]: landpattern.F[22],
                GND[540]: landpattern.F[23],
                GND[541]: landpattern.F[24],
                GND[542]: landpattern.F[29],
                GND[543]: landpattern.F[3],
                GND[544]: landpattern.F[30],
                GND[545]: landpattern.F[31],
                GND[546]: landpattern.F[32],
                GND[547]: landpattern.F[33],
                GND[548]: landpattern.F[34],
                GND[549]: landpattern.F[35],
                GND[550]: landpattern.F[36],
                GND[551]: landpattern.F[37],
                GND[552]: landpattern.F[38],
                GND[553]: landpattern.F[39],
                GND[554]: landpattern.F[40],
                GND[555]: landpattern.F[41],
                GND[556]: landpattern.F[42],
                GND[557]: landpattern.F[43],
                GND[558]: landpattern.F[44],
                GND[559]: landpattern.F[45],
                GND[560]: landpattern.F[46],
                GND[561]: landpattern.F[6],
                GND[562]: landpattern.F[8],
                # Row G
                GND[563]: landpattern.G[10],
                GND[564]: landpattern.G[11],
                GND[565]: landpattern.G[16],
                GND[566]: landpattern.G[21],
                GND[567]: landpattern.G[26],
                GND[568]: landpattern.G[3],
                GND[569]: landpattern.G[31],
                GND[570]: landpattern.G[36],
                GND[571]: landpattern.G[39],
                GND[572]: landpattern.G[4],
                GND[573]: landpattern.G[42],
                GND[574]: landpattern.G[43],
                GND[575]: landpattern.G[44],
                GND[576]: landpattern.G[5],
                GND[577]: landpattern.G[6],
                GND[578]: landpattern.G[8],
                # Row H
                GND[579]: landpattern.H[1],
                GND[580]: landpattern.H[11],
                GND[581]: landpattern.H[13],
                GND[582]: landpattern.H[18],
                GND[583]: landpattern.H[2],
                GND[584]: landpattern.H[23],
                GND[585]: landpattern.H[28],
                GND[586]: landpattern.H[3],
                GND[587]: landpattern.H[33],
                GND[588]: landpattern.H[39],
                GND[589]: landpattern.H[40],
                GND[590]: landpattern.H[41],
                GND[591]: landpattern.H[44],
                GND[592]: landpattern.H[45],
                GND[593]: landpattern.H[46],
                GND[594]: landpattern.H[6],
                GND[595]: landpattern.H[7],
                GND[596]: landpattern.H[9],
                # Row J
                GND[597]: landpattern.J[11],
                GND[598]: landpattern.J[15],
                GND[599]: landpattern.J[20],
                GND[600]: landpattern.J[25],
                GND[601]: landpattern.J[3],
                GND[602]: landpattern.J[30],
                GND[603]: landpattern.J[35],
                GND[604]: landpattern.J[37],
                GND[605]: landpattern.J[38],
                GND[606]: landpattern.J[39],
                GND[607]: landpattern.J[4],
                GND[608]: landpattern.J[42],
                GND[609]: landpattern.J[43],
                GND[610]: landpattern.J[44],
                GND[611]: landpattern.J[5],
                GND[612]: landpattern.J[6],
                GND[613]: landpattern.J[7],
                GND[614]: landpattern.J[9],
                # Row K
                GND[615]: landpattern.K[1],
                GND[616]: landpattern.K[10],
                GND[617]: landpattern.K[11],
                GND[618]: landpattern.K[13],
                GND[619]: landpattern.K[16],
                GND[620]: landpattern.K[19],
                GND[621]: landpattern.K[2],
                GND[622]: landpattern.K[22],
                GND[623]: landpattern.K[25],
                GND[624]: landpattern.K[28],
                GND[625]: landpattern.K[3],
                GND[626]: landpattern.K[31],
                GND[627]: landpattern.K[34],
                GND[628]: landpattern.K[37],
                GND[629]: landpattern.K[40],
                GND[630]: landpattern.K[41],
                GND[631]: landpattern.K[44],
                GND[632]: landpattern.K[45],
                GND[633]: landpattern.K[46],
                GND[634]: landpattern.K[6],
                GND[635]: landpattern.K[8],
                GND[636]: landpattern.K[9],
                # Row L
                GND[637]: landpattern.L[1],
                GND[638]: landpattern.L[11],
                GND[639]: landpattern.L[13],
                GND[640]: landpattern.L[15],
                GND[641]: landpattern.L[17],
                GND[642]: landpattern.L[19],
                GND[643]: landpattern.L[21],
                GND[644]: landpattern.L[23],
                GND[645]: landpattern.L[25],
                GND[646]: landpattern.L[27],
                GND[647]: landpattern.L[29],
                GND[648]: landpattern.L[31],
                GND[649]: landpattern.L[33],
                GND[650]: landpattern.L[35],
                GND[651]: landpattern.L[37],
                GND[652]: landpattern.L[38],
                GND[653]: landpattern.L[39],
                GND[654]: landpattern.L[4],
                GND[655]: landpattern.L[42],
                GND[656]: landpattern.L[43],
                GND[657]: landpattern.L[44],
                GND[658]: landpattern.L[5],
                GND[659]: landpattern.L[6],
                GND[660]: landpattern.L[8],
                GND[661]: landpattern.L[9],
                # Row M
                GND[662]: landpattern.M[1],
                GND[663]: landpattern.M[12],
                GND[664]: landpattern.M[14],
                GND[665]: landpattern.M[16],
                GND[666]: landpattern.M[18],
                GND[667]: landpattern.M[2],
                GND[668]: landpattern.M[20],
                GND[669]: landpattern.M[22],
                GND[670]: landpattern.M[24],
                GND[671]: landpattern.M[26],
                GND[672]: landpattern.M[28],
                GND[673]: landpattern.M[3],
                GND[674]: landpattern.M[30],
                GND[675]: landpattern.M[32],
                GND[676]: landpattern.M[34],
                GND[677]: landpattern.M[36],
                GND[678]: landpattern.M[37],
                GND[679]: landpattern.M[40],
                GND[680]: landpattern.M[41],
                GND[681]: landpattern.M[44],
                GND[682]: landpattern.M[45],
                GND[683]: landpattern.M[46],
                GND[684]: landpattern.M[7],
                GND[685]: landpattern.M[9],
                # Row N
                GND[686]: landpattern.N[1],
                GND[687]: landpattern.N[11],
                GND[688]: landpattern.N[13],
                GND[689]: landpattern.N[15],
                GND[690]: landpattern.N[17],
                GND[691]: landpattern.N[19],
                GND[692]: landpattern.N[21],
                GND[693]: landpattern.N[23],
                GND[694]: landpattern.N[25],
                GND[695]: landpattern.N[27],
                GND[696]: landpattern.N[29],
                GND[697]: landpattern.N[31],
                GND[698]: landpattern.N[33],
                GND[699]: landpattern.N[35],
                GND[700]: landpattern.N[37],
                GND[701]: landpattern.N[38],
                GND[702]: landpattern.N[39],
                GND[703]: landpattern.N[4],
                GND[704]: landpattern.N[42],
                GND[705]: landpattern.N[43],
                GND[706]: landpattern.N[44],
                GND[707]: landpattern.N[5],
                GND[708]: landpattern.N[7],
                GND[709]: landpattern.N[8],
                GND[710]: landpattern.N[9],
                # Row P
                GND[711]: landpattern.P[1],
                GND[712]: landpattern.P[10],
                GND[713]: landpattern.P[12],
                GND[714]: landpattern.P[14],
                GND[715]: landpattern.P[16],
                GND[716]: landpattern.P[18],
                GND[717]: landpattern.P[2],
                GND[718]: landpattern.P[20],
                GND[719]: landpattern.P[22],
                GND[720]: landpattern.P[24],
                GND[721]: landpattern.P[26],
                GND[722]: landpattern.P[28],
                GND[723]: landpattern.P[3],
                GND[724]: landpattern.P[30],
                GND[725]: landpattern.P[32],
                GND[726]: landpattern.P[34],
                GND[727]: landpattern.P[36],
                GND[728]: landpattern.P[37],
                GND[729]: landpattern.P[40],
                GND[730]: landpattern.P[41],
                GND[731]: landpattern.P[44],
                GND[732]: landpattern.P[45],
                GND[733]: landpattern.P[46],
                GND[734]: landpattern.P[6],
                GND[735]: landpattern.P[7],
                GND[736]: landpattern.P[9],
                # Row R
                GND[737]: landpattern.R[10],
                GND[738]: landpattern.R[13],
                GND[739]: landpattern.R[15],
                GND[740]: landpattern.R[17],
                GND[741]: landpattern.R[19],
                GND[742]: landpattern.R[21],
                GND[743]: landpattern.R[23],
                GND[744]: landpattern.R[25],
                GND[745]: landpattern.R[27],
                GND[746]: landpattern.R[29],
                GND[747]: landpattern.R[3],
                GND[748]: landpattern.R[31],
                GND[749]: landpattern.R[33],
                GND[750]: landpattern.R[35],
                GND[751]: landpattern.R[37],
                GND[752]: landpattern.R[38],
                GND[753]: landpattern.R[39],
                GND[754]: landpattern.R[4],
                GND[755]: landpattern.R[40],
                GND[756]: landpattern.R[41],
                GND[757]: landpattern.R[42],
                GND[758]: landpattern.R[43],
                GND[759]: landpattern.R[44],
                GND[760]: landpattern.R[5],
                GND[761]: landpattern.R[7],
                # Row T
                GND[762]: landpattern.T[1],
                GND[763]: landpattern.T[10],
                GND[764]: landpattern.T[11],
                GND[765]: landpattern.T[14],
                GND[766]: landpattern.T[16],
                GND[767]: landpattern.T[18],
                GND[768]: landpattern.T[2],
                GND[769]: landpattern.T[20],
                GND[770]: landpattern.T[22],
                GND[771]: landpattern.T[24],
                GND[772]: landpattern.T[26],
                GND[773]: landpattern.T[28],
                GND[774]: landpattern.T[3],
                GND[775]: landpattern.T[30],
                GND[776]: landpattern.T[37],
                GND[777]: landpattern.T[41],
                GND[778]: landpattern.T[46],
                GND[779]: landpattern.T[6],
                GND[780]: landpattern.T[7],
                GND[781]: landpattern.T[8],
                # Row U
                GND[782]: landpattern.U[11],
                GND[783]: landpattern.U[12],
                GND[784]: landpattern.U[13],
                GND[785]: landpattern.U[15],
                GND[786]: landpattern.U[17],
                GND[787]: landpattern.U[19],
                GND[788]: landpattern.U[21],
                GND[789]: landpattern.U[23],
                GND[790]: landpattern.U[25],
                GND[791]: landpattern.U[27],
                GND[792]: landpattern.U[29],
                GND[793]: landpattern.U[3],
                GND[794]: landpattern.U[31],
                GND[795]: landpattern.U[33],
                GND[796]: landpattern.U[34],
                GND[797]: landpattern.U[35],
                GND[798]: landpattern.U[36],
                GND[799]: landpattern.U[37],
                GND[800]: landpattern.U[38],
                GND[801]: landpattern.U[4],
                GND[802]: landpattern.U[43],
                GND[803]: landpattern.U[5],
                GND[804]: landpattern.U[8],
                # Row V
                GND[805]: landpattern.V[1],
                GND[806]: landpattern.V[10],
                GND[807]: landpattern.V[13],
                GND[808]: landpattern.V[14],
                GND[809]: landpattern.V[16],
                GND[810]: landpattern.V[18],
                GND[811]: landpattern.V[2],
                GND[812]: landpattern.V[20],
                GND[813]: landpattern.V[22],
                GND[814]: landpattern.V[24],
                GND[815]: landpattern.V[26],
                GND[816]: landpattern.V[28],
                GND[817]: landpattern.V[3],
                GND[818]: landpattern.V[30],
                GND[819]: landpattern.V[33],
                GND[820]: landpattern.V[37],
                GND[821]: landpattern.V[40],
                GND[822]: landpattern.V[45],
                GND[823]: landpattern.V[6],
                GND[824]: landpattern.V[7],
                GND[825]: landpattern.V[8],
                GND[826]: landpattern.V[9],
                # Row W
                GND[827]: landpattern.W[11],
                GND[828]: landpattern.W[12],
                GND[829]: landpattern.W[13],
                GND[830]: landpattern.W[15],
                GND[831]: landpattern.W[17],
                GND[832]: landpattern.W[19],
                GND[833]: landpattern.W[21],
                GND[834]: landpattern.W[23],
                GND[835]: landpattern.W[25],
                GND[836]: landpattern.W[27],
                GND[837]: landpattern.W[29],
                GND[838]: landpattern.W[3],
                GND[839]: landpattern.W[31],
                GND[840]: landpattern.W[33],
                GND[841]: landpattern.W[35],
                GND[842]: landpattern.W[37],
                GND[843]: landpattern.W[4],
                GND[844]: landpattern.W[42],
                GND[845]: landpattern.W[5],
                GND[846]: landpattern.W[7],
                GND[847]: landpattern.W[8],
                # Row Y
                GND[848]: landpattern.Y[1],
                GND[849]: landpattern.Y[11],
                GND[850]: landpattern.Y[14],
                GND[851]: landpattern.Y[16],
                GND[852]: landpattern.Y[19],
                GND[853]: landpattern.Y[2],
                GND[854]: landpattern.Y[22],
                GND[855]: landpattern.Y[24],
                GND[856]: landpattern.Y[26],
                GND[857]: landpattern.Y[28],
                GND[858]: landpattern.Y[3],
                GND[859]: landpattern.Y[30],
                GND[860]: landpattern.Y[32],
                GND[861]: landpattern.Y[33],
                GND[862]: landpattern.Y[35],
                GND[863]: landpattern.Y[37],
                GND[864]: landpattern.Y[39],
                GND[865]: landpattern.Y[44],
                GND[866]: landpattern.Y[6],
                GND[867]: landpattern.Y[7],
                GND[868]: landpattern.Y[8],
                # Row AF
                GND_SMON: landpattern.AF[24],
                # Row Y
                GND_VCCINT_SENSE: landpattern.Y[12],
                # Row M
                GND_VCC_AIE_SENSE: landpattern.M[10],
                # Row AE
                GND_VCC_FPD_SENSE: landpattern.AE[19],
                # Row AM
                GND_VCC_SOC_SENSE: landpattern.AM[33],
                # Row W
                GTYP_AVCCAUX_L[0]: landpattern.W[34],
                # Row Y
                GTYP_AVCCAUX_L[1]: landpattern.Y[34],
                # Row V
                GTYP_AVCCAUX_RN[0]: landpattern.V[11],
                GTYP_AVCCAUX_RN[1]: landpattern.V[12],
                # Row AA
                GTYP_AVCC_L[0]: landpattern.AA[34],
                GTYP_AVCC_L[1]: landpattern.AA[35],
                # Row V
                GTYP_AVCC_L[2]: landpattern.V[34],
                GTYP_AVCC_L[3]: landpattern.V[35],
                # Row T
                GTYP_AVCC_RN[0]: landpattern.T[9],
                # Row U
                GTYP_AVCC_RN[1]: landpattern.U[10],
                GTYP_AVCC_RN[2]: landpattern.U[9],
                # Row AA
                GTYP_AVTT_L[0]: landpattern.AA[36],
                # Row V
                GTYP_AVTT_L[1]: landpattern.V[36],
                # Row W
                GTYP_AVTT_L[2]: landpattern.W[36],
                # Row Y
                GTYP_AVTT_L[3]: landpattern.Y[36],
                # Row P
                GTYP_AVTT_RN[0]: landpattern.P[8],
                # Row R
                GTYP_AVTT_RN[1]: landpattern.R[8],
                GTYP_AVTT_RN[2]: landpattern.R[9],
                # Row AJ
                RSVDGND[0]: landpattern.AJ[23],
                RSVDGND[1]: landpattern.AJ[24],
                # Row AG
                VCCAUX[0]: landpattern.AG[26],
                VCCAUX[1]: landpattern.AG[28],
                VCCAUX[2]: landpattern.AG[30],
                # Row AP
                VCCAUX[3]: landpattern.AP[15],
                VCCAUX[4]: landpattern.AP[18],
                VCCAUX[5]: landpattern.AP[21],
                VCCAUX[6]: landpattern.AP[24],
                VCCAUX[7]: landpattern.AP[27],
                VCCAUX[8]: landpattern.AP[30],
                # Row AR
                VCCAUX[9]: landpattern.AR[16],
                VCCAUX[10]: landpattern.AR[19],
                VCCAUX[11]: landpattern.AR[22],
                VCCAUX[12]: landpattern.AR[25],
                VCCAUX[13]: landpattern.AR[28],
                VCCAUX[14]: landpattern.AR[31],
                # Row V
                VCCAUX[15]: landpattern.V[19],
                VCCAUX[16]: landpattern.V[23],
                VCCAUX[17]: landpattern.V[27],
                # Row AE
                VCCAUX_LPD[0]: landpattern.AE[14],
                # Row AF
                VCCAUX_LPD[1]: landpattern.AF[14],
                # Row AT
                VCCAUX_PLL[0]: landpattern.AT[18],
                VCCAUX_PLL[1]: landpattern.AT[21],
                VCCAUX_PLL[2]: landpattern.AT[27],
                VCCAUX_PLL[3]: landpattern.AT[30],
                # Row AF
                VCCAUX_SMON: landpattern.AF[23],
                # Row AA
                VCCINT[0]: landpattern.AA[14],
                VCCINT[1]: landpattern.AA[16],
                VCCINT[2]: landpattern.AA[18],
                VCCINT[3]: landpattern.AA[20],
                VCCINT[4]: landpattern.AA[22],
                VCCINT[5]: landpattern.AA[24],
                VCCINT[6]: landpattern.AA[26],
                VCCINT[7]: landpattern.AA[28],
                VCCINT[8]: landpattern.AA[30],
                VCCINT[9]: landpattern.AA[32],
                # Row AB
                VCCINT[10]: landpattern.AB[29],
                VCCINT[11]: landpattern.AB[30],
                VCCINT[12]: landpattern.AB[32],
                # Row AC
                VCCINT[13]: landpattern.AC[22],
                VCCINT[14]: landpattern.AC[24],
                VCCINT[15]: landpattern.AC[26],
                VCCINT[16]: landpattern.AC[28],
                VCCINT[17]: landpattern.AC[31],
                # Row AD
                VCCINT[18]: landpattern.AD[22],
                VCCINT[19]: landpattern.AD[23],
                VCCINT[20]: landpattern.AD[25],
                VCCINT[21]: landpattern.AD[27],
                VCCINT[22]: landpattern.AD[29],
                VCCINT[23]: landpattern.AD[30],
                # Row AE
                VCCINT[24]: landpattern.AE[24],
                VCCINT[25]: landpattern.AE[33],
                # Row AF
                VCCINT[26]: landpattern.AF[22],
                VCCINT[27]: landpattern.AF[25],
                VCCINT[28]: landpattern.AF[27],
                VCCINT[29]: landpattern.AF[29],
                VCCINT[30]: landpattern.AF[31],
                # Row AG
                VCCINT[31]: landpattern.AG[22],
                # Row AH
                VCCINT[32]: landpattern.AH[25],
                VCCINT[33]: landpattern.AH[27],
                VCCINT[34]: landpattern.AH[29],
                VCCINT[35]: landpattern.AH[30],
                VCCINT[36]: landpattern.AH[33],
                # Row AJ
                VCCINT[37]: landpattern.AJ[22],
                VCCINT[38]: landpattern.AJ[31],
                # Row AK
                VCCINT[39]: landpattern.AK[22],
                VCCINT[40]: landpattern.AK[23],
                VCCINT[41]: landpattern.AK[25],
                VCCINT[42]: landpattern.AK[27],
                VCCINT[43]: landpattern.AK[29],
                VCCINT[44]: landpattern.AK[30],
                # Row AL
                VCCINT[45]: landpattern.AL[33],
                # Row AM
                VCCINT[46]: landpattern.AM[20],
                VCCINT[47]: landpattern.AM[22],
                VCCINT[48]: landpattern.AM[23],
                VCCINT[49]: landpattern.AM[25],
                VCCINT[50]: landpattern.AM[26],
                VCCINT[51]: landpattern.AM[28],
                VCCINT[52]: landpattern.AM[29],
                VCCINT[53]: landpattern.AM[31],
                # Row V
                VCCINT[54]: landpattern.V[15],
                VCCINT[55]: landpattern.V[17],
                VCCINT[56]: landpattern.V[21],
                VCCINT[57]: landpattern.V[25],
                VCCINT[58]: landpattern.V[29],
                VCCINT[59]: landpattern.V[31],
                VCCINT[60]: landpattern.V[32],
                # Row W
                VCCINT[61]: landpattern.W[14],
                VCCINT[62]: landpattern.W[16],
                VCCINT[63]: landpattern.W[18],
                VCCINT[64]: landpattern.W[20],
                VCCINT[65]: landpattern.W[22],
                VCCINT[66]: landpattern.W[24],
                VCCINT[67]: landpattern.W[26],
                VCCINT[68]: landpattern.W[28],
                VCCINT[69]: landpattern.W[30],
                VCCINT[70]: landpattern.W[32],
                # Row Y
                VCCINT[71]: landpattern.Y[15],
                VCCINT[72]: landpattern.Y[31],
                VCCINT_SENSE: landpattern.Y[13],
                # Row AV
                VCCO_700[0]: landpattern.AV[13],
                VCCO_700[1]: landpattern.AV[14],
                VCCO_700[2]: landpattern.AV[16],
                VCCO_700[3]: landpattern.AV[17],
                VCCO_700[4]: landpattern.AV[19],
                # Row AW
                VCCO_700[5]: landpattern.AW[19],
                # Row K
                VCC_AIE[0]: landpattern.K[15],
                VCC_AIE[1]: landpattern.K[18],
                VCC_AIE[2]: landpattern.K[21],
                VCC_AIE[3]: landpattern.K[24],
                VCC_AIE[4]: landpattern.K[27],
                VCC_AIE[5]: landpattern.K[30],
                VCC_AIE[6]: landpattern.K[33],
                VCC_AIE[7]: landpattern.K[35],
                VCC_AIE[8]: landpattern.K[36],
                # Row L
                VCC_AIE[9]: landpattern.L[10],
                VCC_AIE[10]: landpattern.L[12],
                VCC_AIE[11]: landpattern.L[14],
                VCC_AIE[12]: landpattern.L[16],
                VCC_AIE[13]: landpattern.L[18],
                VCC_AIE[14]: landpattern.L[20],
                VCC_AIE[15]: landpattern.L[22],
                VCC_AIE[16]: landpattern.L[24],
                VCC_AIE[17]: landpattern.L[26],
                VCC_AIE[18]: landpattern.L[28],
                VCC_AIE[19]: landpattern.L[30],
                VCC_AIE[20]: landpattern.L[32],
                VCC_AIE[21]: landpattern.L[34],
                VCC_AIE[22]: landpattern.L[36],
                # Row M
                VCC_AIE[23]: landpattern.M[11],
                VCC_AIE[24]: landpattern.M[13],
                VCC_AIE[25]: landpattern.M[15],
                VCC_AIE[26]: landpattern.M[17],
                VCC_AIE[27]: landpattern.M[19],
                VCC_AIE[28]: landpattern.M[21],
                VCC_AIE[29]: landpattern.M[23],
                VCC_AIE[30]: landpattern.M[25],
                VCC_AIE[31]: landpattern.M[27],
                VCC_AIE[32]: landpattern.M[29],
                VCC_AIE[33]: landpattern.M[31],
                VCC_AIE[34]: landpattern.M[33],
                VCC_AIE[35]: landpattern.M[35],
                # Row N
                VCC_AIE[36]: landpattern.N[12],
                VCC_AIE[37]: landpattern.N[14],
                VCC_AIE[38]: landpattern.N[16],
                VCC_AIE[39]: landpattern.N[18],
                VCC_AIE[40]: landpattern.N[20],
                VCC_AIE[41]: landpattern.N[22],
                VCC_AIE[42]: landpattern.N[24],
                VCC_AIE[43]: landpattern.N[26],
                VCC_AIE[44]: landpattern.N[28],
                VCC_AIE[45]: landpattern.N[30],
                VCC_AIE[46]: landpattern.N[32],
                VCC_AIE[47]: landpattern.N[34],
                VCC_AIE[48]: landpattern.N[36],
                # Row P
                VCC_AIE[49]: landpattern.P[11],
                VCC_AIE[50]: landpattern.P[13],
                VCC_AIE[51]: landpattern.P[15],
                VCC_AIE[52]: landpattern.P[17],
                VCC_AIE[53]: landpattern.P[19],
                VCC_AIE[54]: landpattern.P[21],
                VCC_AIE[55]: landpattern.P[23],
                VCC_AIE[56]: landpattern.P[25],
                VCC_AIE[57]: landpattern.P[27],
                VCC_AIE[58]: landpattern.P[29],
                VCC_AIE[59]: landpattern.P[31],
                VCC_AIE[60]: landpattern.P[33],
                VCC_AIE[61]: landpattern.P[35],
                # Row R
                VCC_AIE[62]: landpattern.R[11],
                VCC_AIE[63]: landpattern.R[12],
                VCC_AIE[64]: landpattern.R[14],
                VCC_AIE[65]: landpattern.R[16],
                VCC_AIE[66]: landpattern.R[18],
                VCC_AIE[67]: landpattern.R[20],
                VCC_AIE[68]: landpattern.R[22],
                VCC_AIE[69]: landpattern.R[24],
                VCC_AIE[70]: landpattern.R[26],
                VCC_AIE[71]: landpattern.R[28],
                VCC_AIE[72]: landpattern.R[30],
                VCC_AIE[73]: landpattern.R[32],
                VCC_AIE[74]: landpattern.R[34],
                VCC_AIE[75]: landpattern.R[36],
                # Row T
                VCC_AIE[76]: landpattern.T[12],
                VCC_AIE[77]: landpattern.T[15],
                VCC_AIE[78]: landpattern.T[17],
                VCC_AIE[79]: landpattern.T[19],
                VCC_AIE[80]: landpattern.T[21],
                VCC_AIE[81]: landpattern.T[23],
                VCC_AIE[82]: landpattern.T[25],
                VCC_AIE[83]: landpattern.T[27],
                VCC_AIE[84]: landpattern.T[29],
                VCC_AIE[85]: landpattern.T[31],
                VCC_AIE[86]: landpattern.T[33],
                VCC_AIE[87]: landpattern.T[35],
                VCC_AIE[88]: landpattern.T[36],
                # Row N
                VCC_AIE_SENSE: landpattern.N[10],
                # Row AM
                VCC_BATT: landpattern.AM[16],
                # Row AA
                VCC_FPD[0]: landpattern.AA[19],
                # Row AB
                VCC_FPD[1]: landpattern.AB[14],
                VCC_FPD[2]: landpattern.AB[15],
                VCC_FPD[3]: landpattern.AB[17],
                VCC_FPD[4]: landpattern.AB[18],
                VCC_FPD[5]: landpattern.AB[20],
                VCC_FPD[6]: landpattern.AB[21],
                # Row AC
                VCC_FPD[7]: landpattern.AC[14],
                VCC_FPD[8]: landpattern.AC[16],
                VCC_FPD[9]: landpattern.AC[17],
                VCC_FPD[10]: landpattern.AC[19],
                VCC_FPD[11]: landpattern.AC[20],
                # Row AD
                VCC_FPD[12]: landpattern.AD[15],
                VCC_FPD[13]: landpattern.AD[16],
                VCC_FPD[14]: landpattern.AD[18],
                VCC_FPD[15]: landpattern.AD[19],
                VCC_FPD[16]: landpattern.AD[21],
                # Row AE
                VCC_FPD[17]: landpattern.AE[12],
                VCC_FPD[18]: landpattern.AE[15],
                VCC_FPD[19]: landpattern.AE[17],
                VCC_FPD[20]: landpattern.AE[18],
                VCC_FPD[21]: landpattern.AE[20],
                VCC_FPD[22]: landpattern.AE[21],
                # Row AF
                VCC_FPD[23]: landpattern.AF[13],
                VCC_FPD[24]: landpattern.AF[16],
                VCC_FPD[25]: landpattern.AF[17],
                VCC_FPD[26]: landpattern.AF[20],
                # Row AG
                VCC_FPD[27]: landpattern.AG[12],
                VCC_FPD[28]: landpattern.AG[13],
                VCC_FPD[29]: landpattern.AG[15],
                VCC_FPD[30]: landpattern.AG[16],
                VCC_FPD[31]: landpattern.AG[18],
                VCC_FPD[32]: landpattern.AG[19],
                VCC_FPD[33]: landpattern.AG[21],
                # Row AH
                VCC_FPD[34]: landpattern.AH[12],
                VCC_FPD[35]: landpattern.AH[14],
                VCC_FPD[36]: landpattern.AH[15],
                VCC_FPD[37]: landpattern.AH[17],
                VCC_FPD[38]: landpattern.AH[18],
                VCC_FPD[39]: landpattern.AH[20],
                VCC_FPD[40]: landpattern.AH[21],
                # Row AJ
                VCC_FPD[41]: landpattern.AJ[16],
                # Row Y
                VCC_FPD[42]: landpattern.Y[17],
                VCC_FPD[43]: landpattern.Y[18],
                VCC_FPD[44]: landpattern.Y[20],
                VCC_FPD[45]: landpattern.Y[21],
                # Row AF
                VCC_FPD_SENSE: landpattern.AF[19],
                # Row AM
                VCC_FUSE: landpattern.AM[14],
                # Row AR
                VCC_IO[0]: landpattern.AR[14],
                VCC_IO[1]: landpattern.AR[17],
                VCC_IO[2]: landpattern.AR[20],
                VCC_IO[3]: landpattern.AR[23],
                VCC_IO[4]: landpattern.AR[26],
                VCC_IO[5]: landpattern.AR[29],
                VCC_IO[6]: landpattern.AR[32],
                # Row AJ
                VCC_LPD[0]: landpattern.AJ[17],
                VCC_LPD[1]: landpattern.AJ[19],
                VCC_LPD[2]: landpattern.AJ[20],
                # Row AK
                VCC_LPD[3]: landpattern.AK[16],
                VCC_LPD[4]: landpattern.AK[19],
                VCC_LPD[5]: landpattern.AK[21],
                # Row AL
                VCC_LPD[6]: landpattern.AL[14],
                # Row AM
                VCC_LPD[7]: landpattern.AM[13],
                VCC_LPD[8]: landpattern.AM[17],
                VCC_LPD[9]: landpattern.AM[19],
                # Row AA
                VCC_MMD[0]: landpattern.AA[31],
                # Row AC
                VCC_MMD[1]: landpattern.AC[32],
                VCC_MMD[2]: landpattern.AC[34],
                VCC_MMD[3]: landpattern.AC[35],
                # Row AD
                VCC_MMD[4]: landpattern.AD[31],
                VCC_MMD[5]: landpattern.AD[33],
                VCC_MMD[6]: landpattern.AD[34],
                # Row AF
                VCC_MMD[7]: landpattern.AF[34],
                VCC_MMD[8]: landpattern.AF[35],
                # Row AG
                VCC_MMD[9]: landpattern.AG[31],
                VCC_MMD[10]: landpattern.AG[33],
                VCC_MMD[11]: landpattern.AG[34],
                # Row AH
                VCC_MMD[12]: landpattern.AH[32],
                # Row AJ
                VCC_MMD[13]: landpattern.AJ[32],
                VCC_MMD[14]: landpattern.AJ[34],
                VCC_MMD[15]: landpattern.AJ[35],
                # Row AK
                VCC_MMD[16]: landpattern.AK[31],
                VCC_MMD[17]: landpattern.AK[33],
                VCC_MMD[18]: landpattern.AK[34],
                # Row AM
                VCC_MMD[19]: landpattern.AM[34],
                VCC_MMD[20]: landpattern.AM[35],
                # Row AB
                VCC_RAM[0]: landpattern.AB[23],
                VCC_RAM[1]: landpattern.AB[25],
                VCC_RAM[2]: landpattern.AB[27],
                # Row AJ
                VCC_RAM[3]: landpattern.AJ[26],
                VCC_RAM[4]: landpattern.AJ[28],
                # Row AE
                VCC_SOC[0]: landpattern.AE[26],
                VCC_SOC[1]: landpattern.AE[28],
                VCC_SOC[2]: landpattern.AE[30],
                VCC_SOC[3]: landpattern.AE[35],
                # Row AH
                VCC_SOC[4]: landpattern.AH[35],
                # Row AL
                VCC_SOC[5]: landpattern.AL[15],
                VCC_SOC[6]: landpattern.AL[18],
                VCC_SOC[7]: landpattern.AL[20],
                VCC_SOC[8]: landpattern.AL[21],
                VCC_SOC[9]: landpattern.AL[23],
                VCC_SOC[10]: landpattern.AL[24],
                VCC_SOC[11]: landpattern.AL[26],
                VCC_SOC[12]: landpattern.AL[27],
                VCC_SOC[13]: landpattern.AL[29],
                VCC_SOC[14]: landpattern.AL[30],
                VCC_SOC[15]: landpattern.AL[35],
                # Row AN
                VCC_SOC[16]: landpattern.AN[13],
                VCC_SOC[17]: landpattern.AN[15],
                VCC_SOC[18]: landpattern.AN[16],
                VCC_SOC[19]: landpattern.AN[18],
                VCC_SOC[20]: landpattern.AN[19],
                VCC_SOC[21]: landpattern.AN[21],
                VCC_SOC[22]: landpattern.AN[22],
                VCC_SOC[23]: landpattern.AN[24],
                VCC_SOC[24]: landpattern.AN[25],
                VCC_SOC[25]: landpattern.AN[27],
                VCC_SOC[26]: landpattern.AN[28],
                VCC_SOC[27]: landpattern.AN[30],
                VCC_SOC[28]: landpattern.AN[31],
                VCC_SOC[29]: landpattern.AN[34],
                # Row AP
                VCC_SOC[30]: landpattern.AP[17],
                VCC_SOC[31]: landpattern.AP[20],
                VCC_SOC[32]: landpattern.AP[23],
                VCC_SOC[33]: landpattern.AP[26],
                VCC_SOC[34]: landpattern.AP[29],
                VCC_SOC[35]: landpattern.AP[32],
                VCC_SOC[36]: landpattern.AP[33],
                VCC_SOC[37]: landpattern.AP[35],
                # Row AR
                VCC_SOC[38]: landpattern.AR[34],
                # Row K
                VCC_SOC[39]: landpattern.K[14],
                VCC_SOC[40]: landpattern.K[17],
                VCC_SOC[41]: landpattern.K[20],
                VCC_SOC[42]: landpattern.K[23],
                VCC_SOC[43]: landpattern.K[26],
                VCC_SOC[44]: landpattern.K[29],
                VCC_SOC[45]: landpattern.K[32],
                # Row T
                VCC_SOC[46]: landpattern.T[13],
                VCC_SOC[47]: landpattern.T[32],
                VCC_SOC[48]: landpattern.T[34],
                # Row U
                VCC_SOC[49]: landpattern.U[14],
                VCC_SOC[50]: landpattern.U[16],
                VCC_SOC[51]: landpattern.U[18],
                VCC_SOC[52]: landpattern.U[20],
                VCC_SOC[53]: landpattern.U[22],
                VCC_SOC[54]: landpattern.U[24],
                VCC_SOC[55]: landpattern.U[26],
                VCC_SOC[56]: landpattern.U[28],
                VCC_SOC[57]: landpattern.U[30],
                VCC_SOC[58]: landpattern.U[32],
                # Row Y
                VCC_SOC[59]: landpattern.Y[23],
                VCC_SOC[60]: landpattern.Y[25],
                VCC_SOC[61]: landpattern.Y[27],
                VCC_SOC[62]: landpattern.Y[29],
                # Row AN
                VCC_SOC_SENSE: landpattern.AN[33],
                # Row AH
                VN_500: landpattern.AH[24],
                # Row AG
                VP_500: landpattern.AG[23],
                VREFN_500: landpattern.AG[24],
                # Row AH
                VREFP_500: landpattern.AH[23],
            }
        )
    ]


class LPDDR5Packing(Enum):
    """LPDDR5 pinout packing style for the XC2VE3858 X5IO DDR controllers.

    Mirrors the stanza enum `components/xc2ve3858/LPDDR5Packing`.
    `OPTIMUM` is the default and recommended choice when routing space allows.
    """

    OPTIMUM = "Optimum"
    PACKED_LEFT = "PackedLeft"
    PACKED_RIGHT = "PackedRight"


class DQBit(Port):
    """Inner-Provider bundle for one LPDDR5 DQ bit.

    Used by the bit-swap pin-assignment scheme: per (DDRMC × byte_lane ×
    packing), the wrapper circuit creates 8 ``Provide(DQBit_<...>)``
    instances (one per candidate physical pin), and the outer LPDDR5
    Provider's per-packing mapping calls ``self.require(DQBit_<...>)``
    8 times per byte lane to let the JITX solver permute which DQ bit
    lands on which candidate pin.

    Distinct subclasses are generated dynamically per (DDRMC, byte_idx,
    packing) so each pool's Provides only satisfy require()s targeting
    that exact context — see :py:func:`_make_dqbit_class`.
    """

    p = Port()


def _make_dqbit_class(name: str) -> type[DQBit]:
    """Build a fresh :py:class:`DQBit` subclass with a unique ``__name__``.
    JITX's pin-assignment solver pools Provides by class identity, so
    each pool needs its own class object.
    """
    cls = type(name, (DQBit,), {})
    cls.__qualname__ = name
    return cls


# Pin name template helpers — mirror stanza `to-x5io-pin-name`.
_X5IO_MC_LOOKUP: dict[int, tuple[int, int]] = {
    700: (0, 0), 701: (0, 1), 702: (0, 2),
    703: (1, 3), 704: (1, 4), 705: (1, 5),
    710: (2, 0), 711: (2, 1), 712: (2, 2),
    713: (3, 3), 714: (3, 4), 715: (3, 5),
}


def _to_x5io_pin_name(bank: int, lane: int, polarity: str) -> str:
    """Reproduce stanza `to-x5io-pin-name(bank, lane, polarity)` exactly."""
    p = 2 * lane + (1 if polarity == "N" else 0)
    half = bank % 2
    lane_offset = 0 if half == 0 else 16
    lane_str = f"_L{lane + lane_offset}{polarity}"
    xcc = "_XCC" if (lane % 4 == 1) else ""
    gc = "_GC" if (lane == 3) else ""
    octad = lane // 4
    octad_pin = p % 8
    octad_str = f"_H{half}O{octad}P{octad_pin}"
    if bank in _X5IO_MC_LOOKUP:
        mc, mc_pair_idx = _X5IO_MC_LOOKUP[bank]
        mc_p = 32 * mc_pair_idx + p
        mc_str = f"_M{mc}P{mc_p}"
    else:
        mc_str = ""
    return f"IO{lane_str}{xcc}{gc}{octad_str}{mc_str}_{bank}"


# === LPDDR5 packing configurations (mirror stanza const tables) ===
#
# Each config describes how an LPDDR5 x32 dual-rank link maps onto one of the
# five DDR memory controllers (DDRMC) in the Versal device. A DDRMC owns three
# X5IO banks numbered base_bank+0, base_bank+1, base_bank+2. Pin lookups are
# expressed as `(sub_bank_offset, lane, polarity)` triplets; resolved at
# mapping time via `_to_x5io_pin_name(base_bank + sub_bank, lane, polarity)`.

# A "site" tuple: (sub_bank_offset, lane, polarity)
_Site = tuple[int, int, str]


# A lane spec: (sub_bank_offset, wck_lane, rdqs_lane, dmi_lane, dq_lane_list)
# Each DQ lane in the list contributes its P and N pins (8 total = 8 DQ bits).
_LaneCfg = tuple[int, int, int, int, tuple[int, ...]]


# A channel spec: (lane0, lane1, [cs0_site, cs1_site], (ck_sub_bank, ck_lane), [ca0..ca6])
_ChannelCfg = tuple[
    _LaneCfg,
    _LaneCfg,
    tuple[_Site, _Site],
    tuple[int, int],
    tuple[_Site, _Site, _Site, _Site, _Site, _Site, _Site],
]


# A full DDRMC config: (channel0, channel1, reset_site)
_DdrmcCfg = tuple[_ChannelCfg, _ChannelCfg, _Site]


# Y-lane layout for OPTIMUM/PACKED_RIGHT (DQ lanes [0,2,4,6] / [8,10,12,14]):
_DQ_LANES_LO = (0, 2, 4, 6)
_DQ_LANES_HI = (8, 10, 12, 14)


_LPDDR5_OPTIMUM_CFG: _DdrmcCfg = (
    (  # channel 0
        (2, 5, 1, 7, _DQ_LANES_LO),   # lane 0: bank+2, wck=5, rdqs=1, dmi=7
        (2, 13, 9, 11, _DQ_LANES_HI),  # lane 1: bank+2, wck=13, rdqs=9, dmi=11
        ((1, 10, "P"), (1, 11, "P")),  # cs[0], cs[1]
        (1, 15),                        # ck: bank+1, lane 15
        (
            (1, 8, "P"), (1, 8, "N"), (1, 12, "P"), (1, 12, "N"),
            (1, 13, "P"), (1, 14, "P"), (1, 14, "N"),
        ),
    ),
    (  # channel 1
        (0, 5, 1, 7, _DQ_LANES_LO),
        (0, 13, 9, 15, _DQ_LANES_HI),
        ((1, 10, "N"), (1, 11, "N")),
        (1, 9),
        (
            (1, 0, "N"), (1, 1, "P"), (1, 2, "P"), (1, 4, "N"),
            (1, 5, "P"), (1, 6, "P"), (1, 6, "N"),
        ),
    ),
    (1, 4, "P"),  # reset_n
)


_LPDDR5_PACKED_LEFT_CFG: _DdrmcCfg = (
    (  # channel 0
        (0, 1, 5, 3, _DQ_LANES_LO),
        (0, 9, 13, 11, _DQ_LANES_HI),
        ((1, 3, "P"), (2, 2, "P")),
        (1, 15),
        (
            (1, 11, "N"), (0, 15, "N"), (0, 15, "P"), (0, 11, "N"),
            (0, 7, "N"), (0, 7, "P"), (0, 3, "N"),
        ),
    ),
    (  # channel 1
        (1, 5, 1, 7, _DQ_LANES_LO),
        (1, 13, 9, 11, _DQ_LANES_HI),
        ((1, 3, "N"), (2, 2, "N")),
        (2, 1),
        (
            (2, 7, "N"), (2, 7, "P"), (2, 6, "N"), (2, 6, "P"),
            (2, 5, "P"), (2, 4, "N"), (2, 4, "P"),
        ),
    ),
    (1, 7, "N"),
)


_LPDDR5_PACKED_RIGHT_CFG: _DdrmcCfg = (
    (  # channel 0
        (2, 5, 1, 7, _DQ_LANES_LO),
        (2, 13, 9, 15, _DQ_LANES_HI),
        ((0, 15, "P"), (0, 14, "P")),
        (1, 15),
        (
            (1, 11, "N"), (1, 3, "N"), (1, 3, "P"), (2, 7, "N"),
            (2, 11, "N"), (2, 11, "P"), (2, 15, "N"),
        ),
    ),
    (  # channel 1
        (1, 1, 5, 7, _DQ_LANES_LO),
        (1, 9, 13, 11, _DQ_LANES_HI),
        ((0, 15, "N"), (0, 14, "N")),
        (0, 13),
        (
            (0, 11, "N"), (0, 11, "P"), (0, 10, "N"), (0, 10, "P"),
            (0, 9, "P"), (0, 8, "N"), (0, 8, "P"),
        ),
    ),
    (1, 7, "N"),
)


_LPDDR5_CFGS: dict[LPDDR5Packing, _DdrmcCfg] = {
    LPDDR5Packing.OPTIMUM: _LPDDR5_OPTIMUM_CFG,
    LPDDR5Packing.PACKED_LEFT: _LPDDR5_PACKED_LEFT_CFG,
    LPDDR5Packing.PACKED_RIGHT: _LPDDR5_PACKED_RIGHT_CFG,
}


# DDRMC base banks (one per memory controller — 5 total)
X5IO_DDRMC_BASE_BANKS: tuple[int, ...] = (700, 703, 707, 710, 713)


# Versal bank lists — mirror stanza header constants.
GTYP_BANKS: tuple[int, ...] = (105, 106, 107, 205, 206, 207)
GTYP_MMI_BANKS: tuple[int, ...] = (105,)
HDIO_BANKS: tuple[int, ...] = (400, 402)
PMC_MIO_BANKS: tuple[int, ...] = (500, 501)
LPD_MIO_BANKS: tuple[int, ...] = (502,)
MIPI_BANKS: tuple[int, ...] = (507,)
X5IO_BANKS: tuple[int, ...] = tuple(range(700, 716))
# VCCO_700 is shared between banks 700-704; banks 705+ each have their own.
X5IO_VCCO_BANKS: tuple[int, ...] = (
    700, 700, 700, 700, 700,
    705, 706, 707, 708, 709, 710, 711, 712, 713, 714, 715,
)


class XC2VE3858Circuit(Circuit):
    """XC2VE3858 FPGA wrapped with full Versal protocol bundle ports.

    Pass A built a flat-pin component + power rails. Pass B layers on:

    1. The complete Versal protocol bundle library — `gtyp` (6 banks),
       `io_hd` (2), `pmc_mio` (2), `lpd_mio` (1), `mipi` (1), `io_x5` (16),
       plus `usb2`, `usb3`, `jtag`, `i3c_i2c`. Bank-indexed bundles are
       exposed as ``dict[int, BundleType]`` keyed by stanza bank number.
    2. GPIO mass-Provide — every single-ended I/O pin on the protocol
       bundles is registered as an alternative GPIO source via
       ``Provide(GPIO).one_of(...)``. ~735 individual `Provide` objects.
    3. Bundle-internal power rails — `VCCO` for HDIO/PMC/LPD/X5IO banks,
       `VCC` and `VCCIO` for MIPI and USB3 — moved out of the flat
       ``pwr_vcco_*``/``pwr_vcc_mipi_*``/``pwr_vcc_usb3_*`` ports they
       occupied in Pass A and into the bundle subport tree.

    Three ground domains stay distinct, as in Pass A:

    - main GND: all `GND[*]`, `RSVDGND[*]`, every main-rail `Vn`, and
      every bundle's `VCCO.Vn` / `VCC.Vn` / `VCCIO.Vn`
    - SMON analog ground: `pwr_vccaux_smon.Vn` + `GND_SMON` only
    - Kelvin sense returns: each `pwr_*_sense.Vn` ties only to its
      dedicated `GND_VCC*_SENSE` component pin

    Provides up to 5 independent ``LPDDR5(x32, DualRank)`` interfaces —
    one per DDR memory controller (base banks 700, 703, 707, 710, 713).
    Each offers 3 packing options (Optimum / PackedLeft / PackedRight).
    DQ-bit-to-pin assignment within a lane is fixed; see ``_build_lpddr5_mapping``
    docstring for the option (b) recursive-Provide upgrade path that
    would unlock per-DQ-bit pin swapping.
    """

    # ---- Core / fabric power rails ----
    pwr_vccint = Power()
    pwr_vcc_aie = Power()
    pwr_vcc_soc = Power()
    pwr_vcc_ram = Power()
    pwr_vcc_lpd = Power()
    pwr_vcc_fpd = Power()
    pwr_vcc_io = Power()
    pwr_vcc_mmd = Power()
    pwr_vcc_batt = Power()
    pwr_vcc_fuse = Power()
    pwr_vccaux = Power()
    pwr_vccaux_lpd = Power()
    pwr_vccaux_pll = Power()

    # ---- SMON analog (separate ground domain — Vn tied to GND_SMON) ----
    pwr_vccaux_smon = Power()

    # ---- Kelvin sense rails (each has its own dedicated sense ground) ----
    pwr_vccint_sense = Power()
    pwr_vcc_aie_sense = Power()
    pwr_vcc_fpd_sense = Power()
    pwr_vcc_soc_sense = Power()

    # ---- USB2 / PAUX subsystem rails (USB2 uses 3 separate flat power
    #      ports per stanza; USB3 / MIPI rails are subports of their
    #      respective bundles below). ----
    pwr_vcc_paux_504 = Power()
    pwr_vccio_paux_504 = Power()
    pwr_vcc_usb2_504 = Power()
    pwr_vccio_usb2_504 = Power()
    pwr_vccreg_usb2_504 = Power()

    # ---- GTYP transceiver bias / reference pins (stanza ``: pin``
    #      single-net boundary ports — each is one external supply that
    #      ties to multiple component pins internally). ----
    GTYP_AVTTRCAL_L = Port()
    GTYP_RREF_L = Port()
    GTYP_AVCC_L = Port()
    GTYP_AVTT_L = Port()
    GTYP_AVCCAUX_L = Port()
    GTYP_AVTTRCAL_RN = Port()
    GTYP_RREF_RN = Port()
    GTYP_AVCC_RN = Port()
    GTYP_AVTT_RN = Port()
    GTYP_AVCCAUX_RN = Port()
    GTYP_MMI_AVTTRCAL_RS = Port()
    GTYP_MMI_RREF_RS = Port()
    GTYP_MMI_AVCC_RS = Port()
    GTYP_MMI_AVTT_RS = Port()
    GTYP_MMI_AVCCAUX_RS = Port()

    # ---- Configuration bank single-ended boundary pins ----
    DONE = Port()
    ERROR_OUT = Port()
    POR_B = Port()
    PUDC_B = Port()
    REF_CLK = Port()
    RTC_PADI = Port()
    RTC_PADO = Port()
    USB2_TXRTUNE = Port()
    IO_VR_700 = Port()
    VCCO_503 = Port()  # config bank VCCO — stanza ``port VCCO : pin``

    # ---- USB AUX (PAUX subsystem) ----
    USB_AUX = DiffPair()

    # ---- SYSMON single-ended analog inputs (signals, not power) ----
    vp = Port()      # comp.VP_500
    vn = Port()      # comp.VN_500
    vrefp = Port()   # comp.VREFP_500
    vrefn = Port()   # comp.VREFN_500

    def __init__(self):
        self.fpga = XC2VE3858()
        fpga = self.fpga
        # Place the FPGA component at this circuit's origin so it
        # tracks whatever placement the parent design assigns to this
        # XC2VE3858Circuit instance.
        self.place(self.fpga, Transform.translate(0.0, 0.0))

        # Accumulator for all bundle-wiring Nets — JITX would discard
        # them as orphan references otherwise.
        self._bundle_nets: list = []

        # ====================================================================
        # MODE pins — array of 4 single-ended config-bank pins.
        # Class-level lists of Ports get instantiated lazily; assigning here
        # mirrors the stanza ``port MODE : pin[4]`` declaration.
        # ====================================================================
        self.MODE = [Port() for _ in range(4)]

        # ====================================================================
        # Versal protocol bundle ports (dict[int, Bundle] keyed by stanza
        # bank number — matches stanza's ``port FOO : foo-bundle[BANKS]``).
        # ====================================================================
        self.gtyp: dict[int, GTYPQuad] = {
            bank: (GTYPMMIQuad() if bank in GTYP_MMI_BANKS else GTYPQuad())
            for bank in GTYP_BANKS
        }
        self.io_hd: dict[int, HDIOBank] = {bank: HDIOBank() for bank in HDIO_BANKS}
        self.pmc_mio: dict[int, PMCMioBank] = {
            bank: PMCMioBank() for bank in PMC_MIO_BANKS
        }
        self.lpd_mio: dict[int, LPDMioBank] = {
            bank: LPDMioBank() for bank in LPD_MIO_BANKS
        }
        self.mipi: dict[int, MIPIPhy] = {bank: MIPIPhy() for bank in MIPI_BANKS}
        self.io_x5: dict[int, X5IOBank] = {bank: X5IOBank() for bank in X5IO_BANKS}

        self.usb2 = USB2Connector()
        self.usb3 = GTRUSB3()
        self.jtag = JTAG()
        # I3C is electrically a superset of I2C (extra in-band interrupt /
        # daisy-chain semantics, same SCL+SDA wires); the I2C bundle
        # captures the wiring shape. Stanza names this ``I3CI2C : i2c``.
        self.i3c_i2c = I2C()

        # ====================================================================
        # Pass A power rails (every entry: net_name, Power port, comp pins).
        # Bundle-internal rails are wired separately below.
        # ====================================================================
        rail_groups: list[tuple[str, "Power", list]] = [
            # Core / fabric
            ("VCCINT", self.pwr_vccint, [*fpga.VCCINT]),
            ("VCCAUX", self.pwr_vccaux, [*fpga.VCCAUX]),
            ("VCCAUX_LPD", self.pwr_vccaux_lpd, [*fpga.VCCAUX_LPD]),
            ("VCCAUX_PLL", self.pwr_vccaux_pll, [*fpga.VCCAUX_PLL]),
            ("VCC_AIE", self.pwr_vcc_aie, [*fpga.VCC_AIE]),
            ("VCC_SOC", self.pwr_vcc_soc, [*fpga.VCC_SOC]),
            ("VCC_RAM", self.pwr_vcc_ram, [*fpga.VCC_RAM]),
            ("VCC_LPD", self.pwr_vcc_lpd, [*fpga.VCC_LPD]),
            ("VCC_FPD", self.pwr_vcc_fpd, [*fpga.VCC_FPD]),
            ("VCC_IO", self.pwr_vcc_io, [*fpga.VCC_IO]),
            ("VCC_MMD", self.pwr_vcc_mmd, [*fpga.VCC_MMD]),
            ("VCC_BATT", self.pwr_vcc_batt, [fpga.VCC_BATT]),
            ("VCC_FUSE", self.pwr_vcc_fuse, [fpga.VCC_FUSE]),
            # USB2 / PAUX (separate flat ports per stanza)
            ("VCC_PAUX_504", self.pwr_vcc_paux_504, [*fpga.VCC_PAUX_504]),
            ("VCCIO_PAUX_504", self.pwr_vccio_paux_504, [*fpga.VCCIO_PAUX_504]),
            ("VCC_USB2_504", self.pwr_vcc_usb2_504, [*fpga.VCC_USB2_504]),
            ("VCCIO_USB2_504", self.pwr_vccio_usb2_504, [fpga.VCCIO_USB2_504]),
            ("VCCREG_USB2_504", self.pwr_vccreg_usb2_504, [fpga.VCCREG_USB2_504]),
        ]

        gnd_pins: list = [*fpga.GND, *fpga.RSVDGND]
        for name, rail, pins in rail_groups:
            net = Net([rail.Vp, *pins], name=name)
            setattr(self, f"net_{name.lower()}", net)
            gnd_pins.append(rail.Vn)

        # ====================================================================
        # GTYP bundles (transceiver lanes + reference clocks).
        # Stanza names: GTYP_TXP/N{lane}_{bank}, GTYP_RXP/N{lane}_{bank},
        # GTYP_REFCLKP/N{i}_{bank}; with prefix "GTYP_MMI_" for bank 105.
        # ====================================================================
        for bank in GTYP_BANKS:
            prefix = "GTYP_MMI_" if bank in GTYP_MMI_BANKS else "GTYP_"
            quad = self.gtyp[bank]
            for lane in range(4):
                lane_pair = quad.L[lane]
                # TX
                self._bundle_nets.append(Net(
                    [lane_pair.TX.p, getattr(fpga, f"{prefix}TXP{lane}_{bank}")],
                    name=f"{prefix}TXP{lane}_{bank}",
                ))
                self._bundle_nets.append(Net(
                    [lane_pair.TX.n, getattr(fpga, f"{prefix}TXN{lane}_{bank}")],
                    name=f"{prefix}TXN{lane}_{bank}",
                ))
                # RX
                self._bundle_nets.append(Net(
                    [lane_pair.RX.p, getattr(fpga, f"{prefix}RXP{lane}_{bank}")],
                    name=f"{prefix}RXP{lane}_{bank}",
                ))
                self._bundle_nets.append(Net(
                    [lane_pair.RX.n, getattr(fpga, f"{prefix}RXN{lane}_{bank}")],
                    name=f"{prefix}RXN{lane}_{bank}",
                ))
            for i in range(2):
                self._bundle_nets.append(Net(
                    [quad.REFCLK[i].p, getattr(fpga, f"{prefix}REFCLKP{i}_{bank}")],
                    name=f"{prefix}REFCLKP{i}_{bank}",
                ))
                self._bundle_nets.append(Net(
                    [quad.REFCLK[i].n, getattr(fpga, f"{prefix}REFCLKN{i}_{bank}")],
                    name=f"{prefix}REFCLKN{i}_{bank}",
                ))

        # ====================================================================
        # GTYP transceiver power-pin boundary nets (single Port → multi comp pin).
        # Each is a separate analog supply rail — kept distinct from main GND.
        # ====================================================================
        gtyp_pwr_groups: list[tuple[str, "Port", list]] = [
            # Single-pin rails
            ("GTYP_AVTTRCAL_L", self.GTYP_AVTTRCAL_L, [fpga.GTYP_AVTTRCAL_L]),
            ("GTYP_RREF_L", self.GTYP_RREF_L, [fpga.GTYP_RREF_L]),
            ("GTYP_AVTTRCAL_RN", self.GTYP_AVTTRCAL_RN, [fpga.GTYP_AVTTRCAL_RN]),
            ("GTYP_RREF_RN", self.GTYP_RREF_RN, [fpga.GTYP_RREF_RN]),
            ("GTYP_MMI_AVTTRCAL_RS", self.GTYP_MMI_AVTTRCAL_RS,
             [fpga.GTYP_MMI_AVTTRCAL_RS]),
            ("GTYP_MMI_RREF_RS", self.GTYP_MMI_RREF_RS, [fpga.GTYP_MMI_RREF_RS]),
            # Multi-pin rails
            ("GTYP_AVCC_L", self.GTYP_AVCC_L, [*fpga.GTYP_AVCC_L]),
            ("GTYP_AVTT_L", self.GTYP_AVTT_L, [*fpga.GTYP_AVTT_L]),
            ("GTYP_AVCCAUX_L", self.GTYP_AVCCAUX_L, [*fpga.GTYP_AVCCAUX_L]),
            ("GTYP_AVCC_RN", self.GTYP_AVCC_RN, [*fpga.GTYP_AVCC_RN]),
            ("GTYP_AVTT_RN", self.GTYP_AVTT_RN, [*fpga.GTYP_AVTT_RN]),
            ("GTYP_AVCCAUX_RN", self.GTYP_AVCCAUX_RN, [*fpga.GTYP_AVCCAUX_RN]),
            ("GTYP_MMI_AVCC_RS", self.GTYP_MMI_AVCC_RS, [*fpga.GTYP_MMI_AVCC_RS]),
            ("GTYP_MMI_AVTT_RS", self.GTYP_MMI_AVTT_RS, [*fpga.GTYP_MMI_AVTT_RS]),
            ("GTYP_MMI_AVCCAUX_RS", self.GTYP_MMI_AVCCAUX_RS,
             [*fpga.GTYP_MMI_AVCCAUX_RS]),
        ]
        for name, port, pins in gtyp_pwr_groups:
            # Drop `name=` — JITX rejects a Net carrying the same public
            # name as its boundary Port (which owns it already).
            setattr(self, f"net_{name.lower()}", Net([port, *pins]))

        # ====================================================================
        # HDIO banks (11 diff pairs + VCCO).
        # Lane 5/6 carry the special "_HDGC" infix (high-density gigabit clock).
        # ====================================================================
        for bank in HDIO_BANKS:
            hdio = self.io_hd[bank]
            for lane in range(11):
                hdgc = "_HDGC" if 5 <= lane <= 6 else ""
                self._bundle_nets.append(Net(
                    [hdio.L[lane].p, getattr(fpga, f"IO_L{lane}P{hdgc}_{bank}")],
                    name=f"IO_L{lane}P{hdgc}_{bank}",
                ))
                self._bundle_nets.append(Net(
                    [hdio.L[lane].n, getattr(fpga, f"IO_L{lane}N{hdgc}_{bank}")],
                    name=f"IO_L{lane}N{hdgc}_{bank}",
                ))
            self._bundle_nets.append(Net(
                [hdio.VCCO.Vp, *getattr(fpga, f"VCCO_{bank}")],
                name=f"VCCO_{bank}",
            ))
            gnd_pins.append(hdio.VCCO.Vn)

        # ====================================================================
        # PMC MIO banks. Bank 500 has lanes 0..25; bank 501 has 26..51 (in
        # comp-pin numbering) but the bundle indexes 0..25 in either case
        # (offset = (bank % 2) * 26).
        # ====================================================================
        for bank in PMC_MIO_BANKS:
            pmc = self.pmc_mio[bank]
            offset = (bank % 2) * 26
            for lane in range(26):
                self._bundle_nets.append(Net(
                    [pmc.P[lane], getattr(fpga, f"PMC_MIO{lane + offset}_{bank}")],
                    name=f"PMC_MIO{lane + offset}_{bank}",
                ))
            self._bundle_nets.append(Net(
                [pmc.VCCO.Vp, *getattr(fpga, f"VCCO_{bank}")],
                name=f"VCCO_{bank}",
            ))
            gnd_pins.append(pmc.VCCO.Vn)

        # ====================================================================
        # LPD MIO bank (bank 502).
        # ====================================================================
        for bank in LPD_MIO_BANKS:
            lpd = self.lpd_mio[bank]
            for lane in range(26):
                self._bundle_nets.append(Net(
                    [lpd.P[lane], getattr(fpga, f"LPD_MIO{lane}_{bank}")],
                    name=f"LPD_MIO{lane}_{bank}",
                ))
            self._bundle_nets.append(Net(
                [lpd.VCCO.Vp, *getattr(fpga, f"VCCO_{bank}")],
                name=f"VCCO_{bank}",
            ))
            gnd_pins.append(lpd.VCCO.Vn)

        # ====================================================================
        # MIPI bank 507 (REFCLK + 2 lane pairs + VCC + VCCIO).
        # Stanza signal names: MIPI_TXDP/N{lane}_{bank}, MIPI_RXDP/N{lane}_{bank},
        # MIPI_REF_CLKP/N_{bank}, MIPI_RESREF_{bank}.
        # ====================================================================
        for bank in MIPI_BANKS:
            mipi = self.mipi[bank]
            self._bundle_nets.append(Net(
                [mipi.RESREF, getattr(fpga, f"MIPI_RESREF_{bank}")],
                name=f"MIPI_RESREF_{bank}",
            ))
            self._bundle_nets.append(Net(
                [mipi.REFCLK.p, getattr(fpga, f"MIPI_REF_CLKP_{bank}")],
                name=f"MIPI_REF_CLKP_{bank}",
            ))
            self._bundle_nets.append(Net(
                [mipi.REFCLK.n, getattr(fpga, f"MIPI_REF_CLKN_{bank}")],
                name=f"MIPI_REF_CLKN_{bank}",
            ))
            for lane in range(2):
                self._bundle_nets.append(Net(
                    [mipi.L[lane].TX.p, getattr(fpga, f"MIPI_TXDP{lane}_{bank}")],
                    name=f"MIPI_TXDP{lane}_{bank}",
                ))
                self._bundle_nets.append(Net(
                    [mipi.L[lane].TX.n, getattr(fpga, f"MIPI_TXDN{lane}_{bank}")],
                    name=f"MIPI_TXDN{lane}_{bank}",
                ))
                self._bundle_nets.append(Net(
                    [mipi.L[lane].RX.p, getattr(fpga, f"MIPI_RXDP{lane}_{bank}")],
                    name=f"MIPI_RXDP{lane}_{bank}",
                ))
                self._bundle_nets.append(Net(
                    [mipi.L[lane].RX.n, getattr(fpga, f"MIPI_RXDN{lane}_{bank}")],
                    name=f"MIPI_RXDN{lane}_{bank}",
                ))
            self._bundle_nets.append(Net(
                [mipi.VCCIO.Vp, *getattr(fpga, f"VCCIO_MIPI_{bank}")],
                name=f"VCCIO_MIPI_{bank}",
            ))
            self._bundle_nets.append(Net(
                [mipi.VCC.Vp, *getattr(fpga, f"VCC_MIPI_{bank}")],
                name=f"VCC_MIPI_{bank}",
            ))
            gnd_pins.append(mipi.VCCIO.Vn)
            gnd_pins.append(mipi.VCC.Vn)

        # ====================================================================
        # X5IO banks (700..715, 16 diff pairs each + shared VCCO).
        # Pin-name convention is computed by `_to_x5io_pin_name` (mirrors
        # stanza `to-x5io-pin-name`).
        # ====================================================================
        # Build VCCO net partners — banks 700-704 share VCCO_700.
        x5io_vcco_groups: dict[int, list] = {}
        for bank, vcco_bank in zip(X5IO_BANKS, X5IO_VCCO_BANKS, strict=True):
            x5io = self.io_x5[bank]
            for lane in range(16):
                p_name = _to_x5io_pin_name(bank, lane, "P")
                n_name = _to_x5io_pin_name(bank, lane, "N")
                # Use `>>` (TopologyNet) instead of plain `Net` so the
                # X5IO bank lane port and the physical FPGA pin stay
                # connected through the topology chain — required for
                # downstream LPDDR5 signal-integrity constraints to
                # find a complete path from a bundle leaf through this
                # bank's Provide to the physical pad.
                self._bundle_nets.append(x5io.L[lane].p >> getattr(fpga, p_name))
                self._bundle_nets.append(x5io.L[lane].n >> getattr(fpga, n_name))
            x5io_vcco_groups.setdefault(vcco_bank, []).append(x5io.VCCO.Vp)
            gnd_pins.append(x5io.VCCO.Vn)
        for vcco_bank, vp_ports in x5io_vcco_groups.items():
            self._bundle_nets.append(Net(
                [*vp_ports, *getattr(fpga, f"VCCO_{vcco_bank}")],
                name=f"VCCO_{vcco_bank}",
            ))

        # ====================================================================
        # Configuration bank 503 (single-ended boundary pins + JTAG + I3C/I2C).
        # ====================================================================
        config_singles: list[tuple[str, "Port", "Port"]] = [
            ("DONE_503", self.DONE, fpga.DONE_503),
            ("ERROR_OUT_503", self.ERROR_OUT, fpga.ERROR_OUT_503),
            ("POR_B_503", self.POR_B, fpga.POR_B_503),
            ("PUDC_B_503", self.PUDC_B, fpga.PUDC_B_503),
            ("REF_CLK_503", self.REF_CLK, fpga.REF_CLK_503),
            ("RTC_PADI_503", self.RTC_PADI, fpga.RTC_PADI_503),
            ("RTC_PADO_503", self.RTC_PADO, fpga.RTC_PADO_503),
        ]
        for name, port, comp_pin in config_singles:
            setattr(self, f"net_{name.lower()}", Net([port, comp_pin], name=name))

        for i in range(4):
            self._bundle_nets.append(Net([self.MODE[i], getattr(fpga, f"MODE{i}_503")], name=f"MODE{i}_503"))

        # JTAG
        self._bundle_nets.append(Net([self.jtag.tck, fpga.TCK_503], name="TCK_503"))
        self._bundle_nets.append(Net([self.jtag.tdi, fpga.TDI_503], name="TDI_503"))
        self._bundle_nets.append(Net([self.jtag.tdo, fpga.TDO_503], name="TDO_503"))
        self._bundle_nets.append(Net([self.jtag.tms, fpga.TMS_503], name="TMS_503"))

        # I3C / I2C
        self._bundle_nets.append(Net([self.i3c_i2c.scl, fpga.I3CI2C_SCL_503], name="I3CI2C_SCL_503"))
        self._bundle_nets.append(Net([self.i3c_i2c.sda, fpga.I3CI2C_SDA_503], name="I3CI2C_SDA_503"))

        # Configuration-bank VCCO — single boundary Port tied to comp pins.
        # No `name=`: boundary Port already owns the public name.
        self._bundle_nets.append(Net(
            [self.VCCO_503, *fpga.VCCO_503],
        ))

        # ====================================================================
        # USB AUX, USB2 connector, USB3 (gtr-usb3 bundle), USB2_TXRTUNE.
        # ====================================================================
        self._bundle_nets.append(Net([self.USB_AUX.p, fpga.USB_AUXP_504], name="USB_AUXP_504"))
        self._bundle_nets.append(Net([self.USB_AUX.n, fpga.USB_AUXN_504], name="USB_AUXN_504"))

        # USB2 connector
        self._bundle_nets.append(Net([self.usb2.vbus.Vp, fpga.USB2_VBUS0_504], name="USB2_VBUS0_504"))
        gnd_pins.append(self.usb2.vbus.Vn)
        self._bundle_nets.append(Net([self.usb2.bus.data.p, fpga.USB2_DP0_504], name="USB2_DP0_504"))
        self._bundle_nets.append(Net([self.usb2.bus.data.n, fpga.USB2_DN0_504], name="USB2_DN0_504"))
        self._bundle_nets.append(Net([self.usb2.id, fpga.USB2_ID0_504], name="USB2_ID0_504"))
        self._bundle_nets.append(Net([self.USB2_TXRTUNE, fpga.USB2_TXRTUNE_504], name="USB2_TXRTUNE_504"))

        # USB3 (GTRUSB3): REFCLK, RESREF, sparse TX[0,3] + TXRX[1,2], VCC, VCCIO
        self._bundle_nets.append(Net([self.usb3.REFCLK.p, fpga.USB3_REF_CLKP_504], name="USB3_REF_CLKP_504"))
        self._bundle_nets.append(Net([self.usb3.REFCLK.n, fpga.USB3_REF_CLKN_504], name="USB3_REF_CLKN_504"))
        self._bundle_nets.append(Net([self.usb3.RESREF, fpga.USB3_RESREF_504], name="USB3_RESREF_504"))
        self._bundle_nets.append(Net([self.usb3.TX[0].p, fpga.USB3_TXP0_504], name="USB3_TXP0_504"))
        self._bundle_nets.append(Net([self.usb3.TX[0].n, fpga.USB3_TXN0_504], name="USB3_TXN0_504"))
        self._bundle_nets.append(Net([self.usb3.TX[3].p, fpga.USB3_TXP3_504], name="USB3_TXP3_504"))
        self._bundle_nets.append(Net([self.usb3.TX[3].n, fpga.USB3_TXN3_504], name="USB3_TXN3_504"))
        self._bundle_nets.append(Net([self.usb3.TXRX[1].p, fpga.USB3_TXRXP1_504], name="USB3_TXRXP1_504"))
        self._bundle_nets.append(Net([self.usb3.TXRX[1].n, fpga.USB3_TXRXN1_504], name="USB3_TXRXN1_504"))
        self._bundle_nets.append(Net([self.usb3.TXRX[2].p, fpga.USB3_TXRXP2_504], name="USB3_TXRXP2_504"))
        self._bundle_nets.append(Net([self.usb3.TXRX[2].n, fpga.USB3_TXRXN2_504], name="USB3_TXRXN2_504"))
        self._bundle_nets.append(Net(
            [self.usb3.VCCIO.Vp, *fpga.VCCIO_USB3_504],
            name="VCCIO_USB3_504",
        ))
        self._bundle_nets.append(Net(
            [self.usb3.VCC.Vp, *fpga.VCC_USB3_504],
            name="VCC_USB3_504",
        ))
        gnd_pins.append(self.usb3.VCCIO.Vn)
        gnd_pins.append(self.usb3.VCC.Vn)

        # ====================================================================
        # IO_VR_700 — single-pin boundary for X5IO bank 700 voltage regulator.
        # ====================================================================
        self._bundle_nets.append(Net([self.IO_VR_700, fpga.IO_VR_700]))

        # ====================================================================
        # Main board ground — every accumulated rail Vn lands here.
        # SMON and sense grounds stay separate.
        # ====================================================================
        self.gnd_net = Net(gnd_pins, name="GND")

        # SMON analog ground.
        self.net_vccaux_smon = Net(
            [self.pwr_vccaux_smon.Vp, fpga.VCCAUX_SMON],
            name="VCCAUX_SMON",
        )
        self.net_gnd_smon = Net(
            [self.pwr_vccaux_smon.Vn, fpga.GND_SMON],
            name="GND_SMON",
        )

        # Kelvin sense rails.
        sense_rails: list[tuple[str, "Power", "Port", "Port"]] = [
            ("VCCINT_SENSE", self.pwr_vccint_sense,
             fpga.VCCINT_SENSE, fpga.GND_VCCINT_SENSE),
            ("VCC_AIE_SENSE", self.pwr_vcc_aie_sense,
             fpga.VCC_AIE_SENSE, fpga.GND_VCC_AIE_SENSE),
            ("VCC_FPD_SENSE", self.pwr_vcc_fpd_sense,
             fpga.VCC_FPD_SENSE, fpga.GND_VCC_FPD_SENSE),
            ("VCC_SOC_SENSE", self.pwr_vcc_soc_sense,
             fpga.VCC_SOC_SENSE, fpga.GND_VCC_SOC_SENSE),
        ]
        for name, rail, vp_pin, vn_pin in sense_rails:
            setattr(self, f"net_{name.lower()}",
                    self._bundle_nets.append(Net([rail.Vp, vp_pin], name=name)))
            setattr(self, f"net_gnd_{name.lower()}",
                    self._bundle_nets.append(Net([rail.Vn, vn_pin], name=f"GND_{name}")))

        # SYSMON analog single-ended boundary pins.
        self.net_vp = self.vp + fpga.VP_500
        self.net_vn = self.vn + fpga.VN_500
        self.net_vrefp = self.vrefp + fpga.VREFP_500
        self.net_vrefn = self.vrefn + fpga.VREFN_500

        # ====================================================================
        # GPIO mass-Provide — every single-ended I/O pin on the protocol
        # bundles is registered as a GPIO source. Mirrors stanza
        # `make-gpio-supports`. We target the *bundle subport* rather than
        # the comp pin so pin-assignment routes through the bundle.
        # ====================================================================
        gpio_pins: list = []
        for bank in GTYP_BANKS:
            quad = self.gtyp[bank]
            for lane in range(4):
                gpio_pins.extend([
                    quad.L[lane].TX.p, quad.L[lane].TX.n,
                    quad.L[lane].RX.p, quad.L[lane].RX.n,
                ])
        for bank in HDIO_BANKS:
            for lane in range(11):
                gpio_pins.extend([self.io_hd[bank].L[lane].p, self.io_hd[bank].L[lane].n])
        for bank in PMC_MIO_BANKS:
            for pin_idx in range(25):  # stanza: `for pin in 0 to 25` → 25 iterations
                gpio_pins.append(self.pmc_mio[bank].P[pin_idx])
        for bank in LPD_MIO_BANKS:
            for pin_idx in range(25):
                gpio_pins.append(self.lpd_mio[bank].P[pin_idx])
        for bank in MIPI_BANKS:
            for lane in range(2):
                gpio_pins.extend([
                    self.mipi[bank].L[lane].TX.p, self.mipi[bank].L[lane].TX.n,
                    self.mipi[bank].L[lane].RX.p, self.mipi[bank].L[lane].RX.n,
                ])
        for bank in X5IO_BANKS:
            for lane in range(16):
                gpio_pins.extend([self.io_x5[bank].L[lane].p, self.io_x5[bank].L[lane].n])

        self.gpio_provides = [
            Provide(GPIO).one_of(lambda b, pin=pin: [{b.gpio: pin}])
            for pin in gpio_pins
        ]

        # ====================================================================
        # DQ bit-swap inner Provides — applied to every DDRMC.
        # For each (base_bank, byte_idx, packing) we register 8
        # `Provide(DQBitClass).one_of` instances, one per candidate
        # physical FPGA pin. The outer LPDDR5 Provider's mapping calls
        # `self.require(DQBitClass)` 8 times per byte lane; the solver
        # then picks any permutation of the 8 candidates onto the 8 DQ
        # bits, enabling bit swap within the byte.
        #
        # Pool size: 5 DDRMCs × 4 byte lanes × 3 packings × 8 candidate
        # pins = 480 inner Provides. Each pool of 8 has exactly 8
        # require()s consuming it (one per DQ bit), so the solver only
        # has to permute within each pool — 8! permutations × 60 pools.
        # ====================================================================
        self._dq_swap_classes: dict[tuple[int, int, LPDDR5Packing], type[DQBit]] = {}
        self._dq_swap_inner_provides: list = []
        for base_bank in X5IO_DDRMC_BASE_BANKS:
            for byte_idx in range(4):
                for packing in LPDDR5Packing:
                    cls_name = f"DQBit_{base_bank}_b{byte_idx}_{packing.name}"
                    DQBitCls = _make_dqbit_class(cls_name)
                    self._dq_swap_classes[(base_bank, byte_idx, packing)] = DQBitCls

                    # Compute the 8 candidate (bank, lane, polarity)
                    # sites for this byte lane in this packing.
                    ch0, ch1, _ = _LPDDR5_CFGS[packing]
                    ch_idx, lane_idx = byte_idx // 2, byte_idx % 2
                    ch_cfg = ch0 if ch_idx == 0 else ch1
                    lane_cfg = ch_cfg[lane_idx]
                    sub_bank, _wck, _rdqs, _dmi, dq_lanes = lane_cfg

                    for dq_lane in dq_lanes:
                        for polarity in ("P", "N"):
                            pin = self._x5io_port(
                                base_bank + sub_bank, dq_lane, polarity,
                            )
                            self._dq_swap_inner_provides.append(
                                Provide(DQBitCls).one_of(
                                    lambda b, p=pin: [{b.p: p}]
                                )
                            )

        # ====================================================================
        # Provide one LPDDR5 link per DDRMC, with 3 packing options
        # each. Every DDRMC uses the with-swap mapping so the JITX
        # solver can permute DQ bits within each byte lane.
        # ====================================================================
        self.lpddr5_providers = [
            Provide(LPDDR5(LPDDR5Width.x32, LPDDR5Rank.DualRank)).one_of(
                lambda b, bb=base_bank: [
                    self._build_lpddr5_mapping_with_swap(b, bb, packing)
                    for packing in LPDDR5Packing
                ]
            )
            for base_bank in X5IO_DDRMC_BASE_BANKS
        ]

    # ------------------------------------------------------------------
    # LPDDR5 mapping construction
    # ------------------------------------------------------------------

    def _x5io_port(self, bank: int, lane: int, polarity: str) -> Port:
        """Resolve an X5IO bank/lane/polarity triplet to a component Port."""
        name = _to_x5io_pin_name(bank, lane, polarity)
        return getattr(self.fpga, name)

    def _build_lpddr5_mapping(
        self, b: LPDDR5, base_bank: int, packing: LPDDR5Packing
    ) -> dict:
        """Build a flat LPDDR5 → FPGA pin mapping for one DDRMC + packing.

        Implementation choice: **option (a) — flat per-packing mapping with
        fixed DQ-bit-to-pin assignment**. The 8 DQ bits of each lane are
        assigned in a fixed P-then-N order across the four candidate X5IO
        lanes. Pass A and Pass B both use this option.

        --------------------------------------------------------------------
        Option (b) upgrade — recursive Provide for per-DQ-bit pin swap
        --------------------------------------------------------------------
        Stanza ``make-lpddr5-supports`` (lines 2841–2951 of
        ``xc2ve3858.stanza``) gives the backend per-bit DQ pin selection
        via a 3-level Provide / require pattern. To implement option (b)
        in Python, the call site here would be replaced by:

        1. **Inner per-bit Provides** — one ``Provide(DQBit).one_of(...)``
           per (DDRMC × lane × candidate_pin). For OPTIMUM packing on
           ``base_bank=700`` lane y0, that's 8 inner providers (4 X5IO
           lanes × {P, N}) each registering a single ``{b.p: pin}`` option.
        2. **Mid-level lane Provides** — a ``@provide(Ch0Lane)`` /
           ``@provide(Ch1Lane)`` decorator on a method that calls
           ``self.require(DQBit)`` 8 times, mapping the 8 returned ports
           to ``lane.dq[0..7]``. Same method also fixes ``lane.dmi``,
           ``lane.wck``, ``lane.rdqs`` from the packing config.
        3. **Outer LPDDR5 Provide** — a ``@provide(LPDDR5)`` decorator on
           a method that calls ``self.require(Ch0Lane)`` twice and
           ``self.require(Ch1Lane)`` twice, plus 7 × ``self.require(CABit)``
           per channel and fixed sites for CK / CS / reset_n.

        Constraints:

        - Each ``DQBit`` / ``Ch0Lane`` / ``Ch1Lane`` / ``CABit`` must be a
          distinct Python class per DDRMC (the JITX backend identifies
          provide pools by class identity).
        - Inner Provides must be created *before* the outer ``@provide``
          decorator runs — typically by emitting them in ``__init__``
          before any ``self.require(...)`` calls in the outer provider.
        - Cost: 5 DDRMCs × ~32 inner providers + 4 mid + 1 outer = ~185
          additional ``Provide`` objects per DDRMC family. Routing-time
          search space grows by ~8⁸ per lane.

        Functional gain: backend can swap which X5IO lane drives which
        DQ bit, easing routing congestion in the BGA escape. For Pass B
        we judged the routing benefit not worth the search-space and
        code-complexity costs; option (b) remains a clean upgrade path.
        """
        ch0, ch1, reset_site = _LPDDR5_CFGS[packing]
        mapping: dict = {}

        # Reset
        rs_bank, rs_lane, rs_pol = reset_site
        mapping[b.reset_n] = self._x5io_port(base_bank + rs_bank, rs_lane, rs_pol)

        for ch_idx, ch_cfg in ((0, ch0), (1, ch1)):
            lane0_cfg, lane1_cfg, cs_sites, ck_pos, ca_sites = ch_cfg

            # Data lanes
            for lane_idx, lane_cfg in ((0, lane0_cfg), (1, lane1_cfg)):
                sub_bank, wck_lane, rdqs_lane, dmi_lane, dq_lanes = lane_cfg
                bank = base_bank + sub_bank
                lane = b.d[ch_idx][lane_idx]

                # DQ bits — 4 lanes × {P, N} = 8 bits
                bit = 0
                for dq_lane in dq_lanes:
                    for polarity in ("P", "N"):
                        mapping[lane.dq[bit]] = self._x5io_port(bank, dq_lane, polarity)
                        bit += 1

                # WCK (P/N pair)
                mapping[lane.wck.p] = self._x5io_port(bank, wck_lane, "P")
                mapping[lane.wck.n] = self._x5io_port(bank, wck_lane, "N")

                # RDQS (P/N pair)
                mapping[lane.rdqs.p] = self._x5io_port(bank, rdqs_lane, "P")
                mapping[lane.rdqs.n] = self._x5io_port(bank, rdqs_lane, "N")

                # DMI — single P pin
                mapping[lane.dmi] = self._x5io_port(bank, dmi_lane, "P")

            # CS — two sites, one per rank
            for rank_idx, (cs_bank, cs_lane, cs_pol) in enumerate(cs_sites):
                mapping[b.cs[ch_idx][rank_idx]] = self._x5io_port(
                    base_bank + cs_bank, cs_lane, cs_pol
                )

            # CK — diff pair at (sub_bank, lane), both P and N
            ck_sub, ck_lane = ck_pos
            mapping[b.ck[ch_idx].p] = self._x5io_port(base_bank + ck_sub, ck_lane, "P")
            mapping[b.ck[ch_idx].n] = self._x5io_port(base_bank + ck_sub, ck_lane, "N")

            # CA — 7 single-ended sites
            for ca_idx, (ca_bank, ca_lane, ca_pol) in enumerate(ca_sites):
                mapping[b.ca[ch_idx][ca_idx]] = self._x5io_port(
                    base_bank + ca_bank, ca_lane, ca_pol
                )

        return mapping

    def _build_lpddr5_mapping_with_swap(
        self, b: LPDDR5, base_bank: int, packing: LPDDR5Packing
    ) -> dict:
        """Like :py:meth:`_build_lpddr5_mapping` but routes the 8 DQ bits
        of each byte lane through inner :py:class:`DQBit` Providers so
        the JITX solver can permute which candidate pin lands on which
        DQ index. Non-DQ signals (CK, CS, CA, WCK, RDQS, DMI, RESET_N)
        keep the fixed packing assignment.

        Requires the wrapper circuit to have populated
        ``self._dq_swap_classes`` and ``self._dq_swap_inner_provides``
        for ``base_bank`` before this method runs.
        """
        ch0, ch1, reset_site = _LPDDR5_CFGS[packing]
        mapping: dict = {}

        # Reset
        rs_bank, rs_lane, rs_pol = reset_site
        mapping[b.reset_n] = self._x5io_port(base_bank + rs_bank, rs_lane, rs_pol)

        for ch_idx, ch_cfg in ((0, ch0), (1, ch1)):
            lane0_cfg, lane1_cfg, cs_sites, ck_pos, ca_sites = ch_cfg

            # Data lanes — DQ bits go through inner DQBit Providers.
            for lane_idx, lane_cfg in ((0, lane0_cfg), (1, lane1_cfg)):
                sub_bank, wck_lane, rdqs_lane, dmi_lane, _dq_lanes = lane_cfg
                bank = base_bank + sub_bank
                lane = b.d[ch_idx][lane_idx]
                byte_idx = ch_idx * 2 + lane_idx

                DQBitCls = self._dq_swap_classes[(base_bank, byte_idx, packing)]
                for dq_idx in range(8):
                    dq_bundle = self.require(DQBitCls)
                    mapping[lane.dq[dq_idx]] = dq_bundle.p

                # WCK / RDQS / DMI keep fixed packing assignment.
                mapping[lane.wck.p] = self._x5io_port(bank, wck_lane, "P")
                mapping[lane.wck.n] = self._x5io_port(bank, wck_lane, "N")
                mapping[lane.rdqs.p] = self._x5io_port(bank, rdqs_lane, "P")
                mapping[lane.rdqs.n] = self._x5io_port(bank, rdqs_lane, "N")
                mapping[lane.dmi] = self._x5io_port(bank, dmi_lane, "P")

            # CS — two sites, one per rank
            for rank_idx, (cs_bank, cs_lane, cs_pol) in enumerate(cs_sites):
                mapping[b.cs[ch_idx][rank_idx]] = self._x5io_port(
                    base_bank + cs_bank, cs_lane, cs_pol
                )

            # CK
            ck_sub, ck_lane = ck_pos
            mapping[b.ck[ch_idx].p] = self._x5io_port(base_bank + ck_sub, ck_lane, "P")
            mapping[b.ck[ch_idx].n] = self._x5io_port(base_bank + ck_sub, ck_lane, "N")

            # CA — 7 single-ended sites
            for ca_idx, (ca_bank, ca_lane, ca_pol) in enumerate(ca_sites):
                mapping[b.ca[ch_idx][ca_idx]] = self._x5io_port(
                    base_bank + ca_bank, ca_lane, ca_pol
                )

        return mapping

