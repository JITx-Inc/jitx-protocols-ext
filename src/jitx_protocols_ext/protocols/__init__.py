# Protocol Bundles
#
# This package contains protocol bundle definitions for various interfaces.

from .jesd204 import (
    JESD204,
    JESD204Constraint,
    JESD204LaneCount,
    JESD204Standard,
    JESD204Version,
)
from .pcie import (
    PCIe,
    PCIeConstraint,
    PCIeControl,
    PCIeData,
    PCIeStandard,
    PCIeVersion,
    PCIeWidth,
    connect_pcie_null_modem,
)
from .sata import SATA, connect_sata
from .sfp import (
    QSFP,
    QSFP_DD,
    SFP,
    SFP_DD,
    SFP_Lane,
    SFPConstraint,
    SFPLink,
    SFPStandard,
    connect_qsfp,
    connect_qsfp_dd,
    connect_sfp,
    connect_sfp_dd,
    link_to_lane_count,
)
from .xilinx_versal import (
    GTRUSB3,
    GTYPMMIQuad,
    GTYPQuad,
    HDIOBank,
    LPDMioBank,
    MIPIPhy,
    PMCMioBank,
    X5IOBank,
)

__all__ = [
    # JESD204
    "JESD204",
    "QSFP",
    "QSFP_DD",
    # SATA
    "SATA",
    # SFP
    "SFP",
    "SFP_DD",
    "JESD204Constraint",
    "JESD204LaneCount",
    "JESD204Standard",
    "JESD204Version",
    # PCIe
    "PCIe",
    "PCIeConstraint",
    "PCIeControl",
    "PCIeData",
    "PCIeStandard",
    "PCIeVersion",
    "PCIeWidth",
    "SFPConstraint",
    "SFPLink",
    "SFPStandard",
    "SFP_Lane",
    "connect_pcie_null_modem",
    "connect_qsfp",
    "connect_qsfp_dd",
    "connect_sata",
    "connect_sfp",
    "connect_sfp_dd",
    "link_to_lane_count",
    # Xilinx Versal
    "GTRUSB3",
    "GTYPMMIQuad",
    "GTYPQuad",
    "HDIOBank",
    "LPDMioBank",
    "MIPIPhy",
    "PMCMioBank",
    "X5IOBank",
]
