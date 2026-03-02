# JITX Protocols Extension Package
#
# This package contains protocol bundles for various high-speed interfaces.
#
# Structure:
#   - protocols/       Protocol bundle definitions
#     - memory/        Memory protocols (DDR4, LPDDR4, LPDDR5, GDDR7)
#     - jesd204.py     JESD204B/C protocol
#     - pcie.py        PCIe protocol
#     - sata.py        SATA protocol
#     - sfp.py         SFP/QSFP protocol

# Re-export protocols for convenience
from .protocols import (
    # JESD204
    JESD204,
    QSFP,
    QSFP_DD,
    # SATA
    SATA,
    # SFP
    SFP,
    SFP_DD,
    JESD204Constraint,
    JESD204LaneCount,
    JESD204Standard,
    JESD204Version,
    # PCIe
    PCIe,
    PCIeConstraint,
    PCIeControl,
    PCIeData,
    PCIeStandard,
    PCIeVersion,
    PCIeWidth,
    SFP_Lane,
    SFPConstraint,
    SFPLink,
    SFPStandard,
    connect_pcie_null_modem,
    connect_qsfp,
    connect_qsfp_dd,
    connect_sata,
    connect_sfp,
    connect_sfp_dd,
    link_to_lane_count,
)
from .protocols.memory import (
    # DDR4
    DDR4,
    # GDDR7
    GDDR7,
    # LPDDR4
    LPDDR4,
    # LPDDR5
    LPDDR5,
    DDR4Constraint,
    DDR4Impedances,
    DDR4Rank,
    DDR4Width,
    GDDR7Constraint,
    GDDR7Impedances,
    LPDDR4Constraint,
    LPDDR4Impedances,
    LPDDR4Rank,
    LPDDR4Width,
    LPDDR5Constraint,
    LPDDR5Impedances,
    LPDDR5Rank,
    LPDDR5Width,
    connect_ddr4,
    connect_gddr7,
    connect_lpddr4,
    connect_lpddr5,
)

__all__ = [
    # DDR4
    "DDR4",
    # GDDR7
    "GDDR7",
    # JESD204
    "JESD204",
    # LPDDR4
    "LPDDR4",
    # LPDDR5
    "LPDDR5",
    "QSFP",
    "QSFP_DD",
    # SATA
    "SATA",
    # SFP
    "SFP",
    "SFP_DD",
    "DDR4Constraint",
    "DDR4Impedances",
    "DDR4Rank",
    "DDR4Width",
    "GDDR7Constraint",
    "GDDR7Impedances",
    "JESD204Constraint",
    "JESD204LaneCount",
    "JESD204Standard",
    "JESD204Version",
    "LPDDR4Constraint",
    "LPDDR4Impedances",
    "LPDDR4Rank",
    "LPDDR4Width",
    "LPDDR5Constraint",
    "LPDDR5Impedances",
    "LPDDR5Rank",
    "LPDDR5Width",
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
    "connect_ddr4",
    "connect_gddr7",
    "connect_lpddr4",
    "connect_lpddr5",
    "connect_pcie_null_modem",
    "connect_qsfp",
    "connect_qsfp_dd",
    "connect_sata",
    "connect_sfp",
    "connect_sfp_dd",
    "link_to_lane_count",
]
