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

# Re-export protocols for backwards compatibility
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
    connect_pcie_null_modem,
)
from .protocols.memory import (
    DDR4,
    GDDR7,
    LPDDR4,
    LPDDR5,
    DDR4Constraint,
    DDR4Rank,
    DDR4Width,
    GDDR7Constraint,
    LPDDR4Constraint,
    LPDDR4Rank,
    LPDDR4Width,
    LPDDR5Constraint,
    LPDDR5Rank,
    LPDDR5Width,
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
    "DDR4Rank",
    "DDR4Width",
    # GDDR7
    "GDDR7",
    "GDDR7Constraint",
    # LPDDR4
    "LPDDR4",
    "LPDDR4Constraint",
    "LPDDR4Rank",
    "LPDDR4Width",
    # LPDDR5
    "LPDDR5",
    "LPDDR5Constraint",
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
    "connect_pcie_null_modem",
    # SATA
    "SATA",
    # SFP
    "SFP",
    "SFP_DD",
    "QSFP",
    "QSFP_DD",
    "SFP_Lane",
    "SFPLink",
    "SFPConstraint",
]
