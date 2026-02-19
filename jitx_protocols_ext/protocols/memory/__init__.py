# Memory Protocols
#
# This package contains memory interface protocol bundles.

from .ddr4 import (
    DDR4,
    DDR4AccChannel,
    DDR4AccConstraint,
    DDR4AccConstraintParams,
    DDR4Constraint,
    DDR4DataAccConstraint,
    DDR4DataAccConstraintParams,
    DDR4DataChannel,
    DDR4DataConstraint,
    DDR4DataConstraintParams,
    DDR4Impedances,
    DDR4Rank,
    DDR4Topology,
    DDR4Width,
    connect_ddr4,
    rank_to_int,
    width_to_int,
    width_to_lane_count,
)
from .gddr7 import (
    GDDR7,
    GDDR7Constraint,
    GDDR7ConstraintParams,
    GDDR7ControlChannel,
    GDDR7DataChannel,
    GDDR7Impedances,
    connect_gddr7,
)
from .lpddr4 import (
    LPDDR4,
    LPDDR4_X16,
    LPDDR4Constraint,
    LPDDR4ConstraintParams,
    LPDDR4Impedances,
    LPDDR4Lane,
    LPDDR4Rank,
    LPDDR4Width,
    connect_lpddr4,
    num_x16_lanes,
)
from .lpddr4 import (
    rank_to_int as lpddr4_rank_to_int,
)
from .lpddr4 import (
    width_to_int as lpddr4_width_to_int,
)
from .lpddr5 import (
    LPDDR5,
    LPDDR5Constraint,
    LPDDR5ConstraintParams,
    LPDDR5DataLane,
    LPDDR5Impedances,
    LPDDR5Rank,
    LPDDR5Width,
    connect_lpddr5,
)
from .lpddr5 import (
    num_channels as lpddr5_num_channels,
)
from .lpddr5 import (
    rank_to_int as lpddr5_rank_to_int,
)
from .lpddr5 import (
    width_to_int as lpddr5_width_to_int,
)

__all__ = [
    # DDR4
    "DDR4",
    # GDDR7
    "GDDR7",
    # LPDDR4
    "LPDDR4",
    "LPDDR4_X16",
    # LPDDR5
    "LPDDR5",
    "DDR4AccChannel",
    "DDR4AccConstraint",
    "DDR4AccConstraintParams",
    "DDR4Constraint",
    "DDR4DataAccConstraint",
    "DDR4DataAccConstraintParams",
    "DDR4DataChannel",
    "DDR4DataConstraint",
    "DDR4DataConstraintParams",
    "DDR4Impedances",
    "DDR4Rank",
    "DDR4Topology",
    "DDR4Width",
    "GDDR7Constraint",
    "GDDR7ConstraintParams",
    "GDDR7ControlChannel",
    "GDDR7DataChannel",
    "GDDR7Impedances",
    "LPDDR4Constraint",
    "LPDDR4ConstraintParams",
    "LPDDR4Impedances",
    "LPDDR4Lane",
    "LPDDR4Rank",
    "LPDDR4Width",
    "LPDDR5Constraint",
    "LPDDR5ConstraintParams",
    "LPDDR5DataLane",
    "LPDDR5Impedances",
    "LPDDR5Rank",
    "LPDDR5Width",
    "connect_ddr4",
    "connect_gddr7",
    "connect_lpddr4",
    "connect_lpddr5",
    "lpddr4_rank_to_int",
    "lpddr4_width_to_int",
    "lpddr5_num_channels",
    "lpddr5_rank_to_int",
    "lpddr5_width_to_int",
    "num_x16_lanes",
    "rank_to_int",
    "width_to_int",
    "width_to_lane_count",
]
