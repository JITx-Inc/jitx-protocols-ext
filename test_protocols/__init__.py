# Test Memory Protocols Package
#
# This package contains protocol bundles and example designs for various interfaces.
#
# Structure:
#   - protocols/       Protocol bundle definitions
#     - memory/        Memory protocols (DDR4, LPDDR4, LPDDR5, GDDR7)
#     - pcie.py        PCIe protocol
#     - sata.py        SATA protocol
#     - sfp.py         SFP/QSFP protocol
#   - examples/        Example designs
#     - protocols/     Protocol-specific examples
#       - memory/      Memory protocol examples
#       - pcie/        PCIe protocol examples
#       - sata/        SATA protocol examples
#       - sfp/         SFP protocol examples
#   - common/          Shared infrastructure
#     - example_board.py      Board and stackup definitions
#     - example_components.py Blocking caps, pull-up resistors

# Re-export protocols for backwards compatibility
from .protocols.memory import (
    DDR4,
    DDR4Constraint,
    DDR4Rank,
    DDR4Width,
    GDDR7,
    GDDR7Constraint,
    LPDDR4,
    LPDDR4Constraint,
    LPDDR4Rank,
    LPDDR4Width,
    LPDDR5,
    LPDDR5Constraint,
    LPDDR5Rank,
    LPDDR5Width,
)

from .protocols import (
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
    # SFP
    SFP,
    SFP_DD,
    QSFP,
    QSFP_DD,
    SFP_Lane,
    SFPLink,
    SFPConstraint,
)

__all__ = [
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
