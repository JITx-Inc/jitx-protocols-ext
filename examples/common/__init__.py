# Common utilities for protocol examples.
#
# Memory-protocol signal tags now live canonically in
# `jitx_protocols_ext.protocols.memory.lpddr_constraints`. Import from
# there directly rather than via this package.

from .example_components import BlockingCapacitor, PullUpResistor
from .generic_fr4_board import (
    ExampleBoard,
    ExampleStackup,
    ExampleSubstrate,
    SE50RoutingStructure,
    create_differential_routing_structure,
)
from .high_perf_board import (
    HighPerfBoard,
    HighPerfStackup,
    HighPerfSubstrate,
)

__all__ = [
    "BlockingCapacitor",
    "ExampleBoard",
    "ExampleStackup",
    "ExampleSubstrate",
    "HighPerfBoard",
    "HighPerfStackup",
    "HighPerfSubstrate",
    "PullUpResistor",
    "SE50RoutingStructure",
    "create_differential_routing_structure",
]
