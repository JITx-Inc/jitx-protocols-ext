# JITX Protocols Extension Package
#
# This package contains protocol bundles and example designs for various interfaces.
#
# Structure:
#   - protocols/       Protocol bundle definitions
#     - memory/        Memory protocols (DDR4, LPDDR4, LPDDR5, GDDR7)
#     - jesd204.py     JESD204B/C protocol
#     - pcie.py        PCIe protocol
#     - sata.py        SATA protocol
#     - sfp.py         SFP/QSFP protocol
#   - examples/        Example designs
#     - protocols/     Protocol-specific examples
#       - jesd204/     JESD204 protocol examples
#       - memory/      Memory protocol examples
#       - pcie/        PCIe protocol examples
#       - sata/        SATA protocol examples
#       - sfp/         SFP protocol examples
#   - common/          Shared infrastructure
#     - example_board.py      Board and stackup definitions
#     - example_components.py Blocking caps, pull-up resistors

# Re-export protocols for convenience
from .protocols import (
    # JESD204
    JESD204,
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
    connect_pcie_null_modem,
    # SATA
    SATA,
    connect_sata,
    # SFP
    SFP,
    SFP_DD,
    QSFP,
    QSFP_DD,
    SFP_Lane,
    SFPConstraint,
    SFPLink,
    SFPStandard,
    connect_sfp,
    connect_sfp_dd,
    connect_qsfp,
    connect_qsfp_dd,
    link_to_lane_count,
)
from .protocols.memory import (
    # DDR4
    DDR4,
    DDR4Constraint,
    DDR4Impedances,
    DDR4Rank,
    DDR4Width,
    connect_ddr4,
    # GDDR7
    GDDR7,
    GDDR7Constraint,
    GDDR7Impedances,
    connect_gddr7,
    # LPDDR4
    LPDDR4,
    LPDDR4Constraint,
    LPDDR4Impedances,
    LPDDR4Rank,
    LPDDR4Width,
    connect_lpddr4,
    # LPDDR5
    LPDDR5,
    LPDDR5Constraint,
    LPDDR5Impedances,
    LPDDR5Rank,
    LPDDR5Width,
    connect_lpddr5,
)

__all__ = [
    # JESD204
    "JESD204",
    "JESD204Constraint",
    "JESD204LaneCount",
    "JESD204Standard",
    "JESD204Version",
    # DDR4
    "DDR4",
    "DDR4Constraint",
    "DDR4Impedances",
    "DDR4Rank",
    "DDR4Width",
    "connect_ddr4",
    # GDDR7
    "GDDR7",
    "GDDR7Constraint",
    "GDDR7Impedances",
    "connect_gddr7",
    # LPDDR4
    "LPDDR4",
    "LPDDR4Constraint",
    "LPDDR4Impedances",
    "LPDDR4Rank",
    "LPDDR4Width",
    "connect_lpddr4",
    # LPDDR5
    "LPDDR5",
    "LPDDR5Constraint",
    "LPDDR5Impedances",
    "LPDDR5Rank",
    "LPDDR5Width",
    "connect_lpddr5",
    # PCIe
    "PCIe",
    "PCIeConstraint",
    "PCIeControl",
    "PCIeData",
    "PCIeStandard",
    "PCIeVersion",
    "PCIeWidth",
    "connect_pcie_null_modem",
    # SATA
    "SATA",
    "connect_sata",
    # SFP
    "SFP",
    "SFP_DD",
    "QSFP",
    "QSFP_DD",
    "SFP_Lane",
    "SFPLink",
    "SFPStandard",
    "SFPConstraint",
    "connect_sfp",
    "connect_sfp_dd",
    "connect_qsfp",
    "connect_qsfp_dd",
    "link_to_lane_count",
]
