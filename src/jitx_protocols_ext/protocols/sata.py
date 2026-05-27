"""SATA Protocol

SATA is a serial protocol supporting high speed links for storage applications.
https://en.wikipedia.org/wiki/SATA

The functions and definitions in this file support defining SATA
connections between sources and receivers on a printed circuit board.

## SATA Generations

- **SATA Revision 1.0**: Top transfer rate of 1.5 Gbps
- **SATA Revision 2.0**: Transfer speed of 3.2 Gbps with port multipliers and improved queue depth
- **SATA Revision 3.0**: Drive transfer rates up to 6 Gbps (backward-compatible with Rev 1 and 2)
- **SATA Revision 3.1**: Added SATA Universal Storage Module requirements
- **SATA Revision 3.2**: Added SATA Express specification with PCIe lane support
- **SATA Revision 3.3**: Addressed shingled magnetic recording
- **SATA Revision 3.5**: Promoted greater integration with PCIe flash and other I/O protocols

## References

- https://sata-io.org/system/files/specifications/SerialATA_Revision_3_1_Gold.pdf

## SATA AC Coupling

The SATA specification typically requires AC coupling for the data lanes using
blocking capacitors. Use the :py:meth:`~jitx.si.SignalConstraint.constrain_topology`
mechanism to add blocking capacitors to the topology.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from jitx import current
from jitx.common import LanePair
from jitx.container import inner
from jitx.net import Port
from jitx.si import DifferentialRoutingStructure, DiffPairConstraint, SignalConstraint
from jitx.toleranced import Toleranced


class SATA(Port):
    """SATA Bundle

    The SATA data bundle consists of 1 lane pair (1 RX and TX differential pair).

    Attributes:
        lane: Lane pair for the SATA bundle (consists of a TX and RX diff pair)
    """

    lane = LanePair()
    "Lane pair for SATA data transfer"

    @dataclass(frozen=True)
    class Standard:
        """SATA Standard Parameters

        Attributes:
            skew: Allowed intra-pair skew in seconds
            loss: Allowed loss in dB
            impedance: Differential impedance (90Ω ±15%)
        """

        skew: Toleranced
        "Allowed intra-pair skew"

        loss = 15.0
        "Allowed loss in dB"

        impedance = Toleranced.percent(90, 15)
        "Differential trace impedance"

    class Generation(Standard, Enum):
        """SATA Generation Specifications

        Different SATA generations with accompanying standard values.
        To customize parameters, use :py:func:`dataclasses.replace`.

        Example:
            >>> import dataclasses
            >>> custom = dataclasses.replace(SATA.Generation.SATA3p0, loss=12.0)
        """

        SATA1p0 = Toleranced(0, 4.0e-12)
        "1.5 Gbit/s"
        SATA2p0 = Toleranced(0, 2.0e-12)
        "3.2 Gbit/s"
        SATA3p0 = Toleranced(0, 1.0e-12)
        "6.0 Gbit/s"
        SATA3p1 = Toleranced(0, 1.0e-12)
        "6.0 Gbit/s"
        SATA3p2 = Toleranced(0, 1.0e-12)
        "6.0 Gbit/s (with SATA Express)"
        SATA3p3 = Toleranced(0, 1.0e-12)
        "6.0 Gbit/s (with SMR support)"
        SATA3p4 = Toleranced(0, 1.0e-12)
        "6.0 Gbit/s"

    @inner
    class Constraint(SignalConstraint["SATA"]):
        """Signal Integrity Constraint for SATA

        This constraint applies intra-pair skew and loss limits to SATA connections.

        Args:
            standard: SATA standard specification containing skew and loss parameters
            structure: Differential routing structure. If not provided, uses substrate default.
        """

        def __init__(
            self,
            standard: SATA.Standard,
            structure: DifferentialRoutingStructure | None = None,
        ):
            if not structure:
                structure = current.substrate.differential_routing_structure(standard.impedance)
            self.diffpair_constraint = DiffPairConstraint(
                skew=standard.skew, loss=standard.loss, structure=structure
            )

        def constrain(self, src: SATA, dst: SATA):
            """Apply constraints to SATA connection

            Args:
                src: Source SATA port
                dst: Destination SATA port
            """
            # Constrain TX path (src TX -> dst RX)
            self.diffpair_constraint.constrain(src.lane.TX, dst.lane.RX)
            # Constrain RX path (src RX <- dst TX)
            self.diffpair_constraint.constrain(src.lane.RX, dst.lane.TX)


def connect_sata(
    src: SATA,
    dst: SATA,
    gen: SATA.Generation = SATA.Generation.SATA3p0,
    structure: DifferentialRoutingStructure | None = None,
):
    """Connect and constrain a SATA link.

    Convenience function that creates a SATA.Constraint and applies it via
    ``constrain_topology``. Equivalent to Stanza's ``connect-SATA``.

    Args:
        src: Source SATA port
        dst: Destination SATA port
        gen: SATA generation (default: SATA3p0)
        structure: Differential routing structure. If None, auto-resolved.

    Returns:
        The SATA.Constraint that was applied.
    """
    constraint = SATA.Constraint(gen, structure=structure)
    constraint.constrain_topology(src, dst)
    return constraint
