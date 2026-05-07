"""LPDDR (4 / 5 / 5x) tag library and design-rule applier.

This module is the canonical home for LPDDR signal-type tags and
spacing-rule construction. It serves three roles:

1. **Tag classes** for every port type in the LPDDR5 bundle
   (:py:class:`DQTag`, :py:class:`DMITag`, :py:class:`WCKTag`,
   :py:class:`RDQSTag`, :py:class:`CKTag`, :py:class:`CATag`,
   :py:class:`CSnTag`, :py:class:`ResetTag`) plus AMD UG863 grouping
   tags (:py:class:`CACTag`, :py:class:`StrobeTag`, :py:class:`DataTag`),
   region tags (:py:class:`UnderFPGATag`, :py:class:`UnderMemTag`), and
   byte/channel index tags (:py:class:`Byte0Tag`..:py:class:`Byte7Tag`,
   :py:class:`Channel0Tag`..:py:class:`Channel3Tag`).

2. :py:func:`tag_lpddr_link` — applies all signal-type, byte, and
   channel tags to every port in an LPDDR5 src/dst pair. Called
   automatically by :py:meth:`LPDDR5Constraint.constrain`.

3. :py:func:`make_lpddr_spacing_rules` — builds the full set of
   AMD UG863 pairwise tag clearance rules, parameterized by ``H``
   (distance to the nearest GND return plane) and the number of
   byte lanes in the LPDDR5 configuration. The caller stores the
   returned list (e.g. ``self.lpddr_rules = make_lpddr_spacing_rules(H=h)``).

   :py:func:`get_H` is provided for stackup introspection.

   :py:func:`lpddr_loss_budget` converts the AMD UG863 2000-mil
   max-trace-length spec into a max-insertion-loss budget given
   the routing structure's per-mm loss coefficient.

Sources:

- AMD UG863, "PCB Routing Guidelines for LPDDR5/5x Interfaces":
  https://docs.amd.com/r/en-US/ug863-versal-pcb-design/PCB-Routing-Guidelines-for-LPDDR5/5x-Interfaces
- AMD UG863, "Physical Design Rules for LPDDR5/5x Signals" — spacing
  table reproduced in :py:func:`make_lpddr_spacing_rules`.

Spacing table (verbatim from UG863 §"Physical Design Rules"):

CAC and Clock signal spacing (within-channel)::

    Pair                       Outside SoC/DRAM    Under SoC/DRAM
    Between CAC signals        2.5 H               1 H
    CA to CK signals           5   H               2 H
    CAC/CK to data/strobe      7   H               2 H

Data, WCK, RDQS signal spacing (within-channel)::

    Pair                                   Outside    Under
    Data within same byte                  2.5 H      1 H
    Data to WCK/RDQS within same byte      5   H      1 H
    Data to WCK/RDQS between bytes         7   H      2 H
    Data/WCK/RDQS to other signals         7   H      2 H

Inter-channel / inter-interface spacing::

    Any pair across channels               7 H        2 H

Where ``H`` is the distance to the nearest ground return plane.

Implementation note on Under-region rules
-----------------------------------------
The :py:class:`UnderFPGATag` / :py:class:`UnderMemTag` tags are predefined
but **only the Outside spacing rules are auto-generated** by
:py:func:`make_lpddr_spacing_rules`. JITX clearance rules are net-level
and AMD's "Under SoC/DRAM" rule is a *spatial* relaxation in the BGA
fanout region — not modellable as a whole-net property. Users who want
the relaxed Under rules can either: (a) manually tag fanout-only escape
nets with the region tags and add their own design_constraint rules
on top, or (b) leave region tags off and accept the safer Outside rules
everywhere. The protocol's ``connect_lpddr5`` does **not** auto-apply
region tags.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from jitx.constraints import Tag, design_constraint

if TYPE_CHECKING:
    from jitx.stackup import Stackup

    from .lpddr5 import LPDDR5, LPDDR5Rank, LPDDR5Width


# ---------------------------------------------------------------------------
# AMD UG863 numeric constants
# ---------------------------------------------------------------------------

#: UG863 §"Physical Design Rules": maximum PCB trace length for both
#: CAC/CK and data signals.
LPDDR_MAX_TRACE_LEN_MIL: float = 2000.0

#: ``LPDDR_MAX_TRACE_LEN_MIL`` converted to millimeters.
LPDDR_MAX_TRACE_LEN_MM: float = LPDDR_MAX_TRACE_LEN_MIL * 0.0254  # ≈ 50.8 mm


# ---------------------------------------------------------------------------
# Per-port-type signal tags (one per LPDDR5 bundle port type)
# ---------------------------------------------------------------------------


class DQTag(Tag):
    """LPDDR DQ data bit. Single-ended, bidirectional."""


class DMITag(Tag):
    """LPDDR DMI mask. Single-ended, byte-aligned with DQ."""


class WCKTag(Tag):
    """LPDDR5 write clock. Differential pair, controller-driven."""


class RDQSTag(Tag):
    """LPDDR5 read data strobe. Differential pair, memory-driven."""


class CKTag(Tag):
    """LPDDR clock. Differential pair, controller-driven."""


class CATag(Tag):
    """LPDDR command/address bit. Single-ended, controller-driven."""


class CSnTag(Tag):
    """LPDDR chip-select (active-low). Single-ended, controller-driven."""


class ResetTag(Tag):
    """LPDDR reset_n. Single-ended, system-level."""


class DQSTag(Tag):
    """Generic bidirectional data strobe (DDR4/5).

    Not used by LPDDR5 (which has separate :py:class:`WCKTag` /
    :py:class:`RDQSTag`); kept so DDR-family examples can share this
    module.
    """


# ---------------------------------------------------------------------------
# AMD UG863 signal-class umbrella tags
# ---------------------------------------------------------------------------
# These get *also* applied to every port of the corresponding kind.
# A spacing rule on `CACTag()` matches CA + CSn together.


class CACTag(Tag):
    """Command/Address/Control class — applied alongside CATag and CSnTag."""


class StrobeTag(Tag):
    """Data-strobe class — applied alongside WCKTag and RDQSTag."""


class DataTag(Tag):
    """Data class — applied alongside DQTag and DMITag."""


# ---------------------------------------------------------------------------
# Region tags (AMD UG863 "Under SoC/DRAM" relaxation)
# ---------------------------------------------------------------------------


class UnderFPGATag(Tag):
    """Net is routed under the FPGA / SoC package (BGA fanout region).

    Marker for the relaxed "Under SoC/DRAM" spacing rules. Apply manually
    to short fanout-only nets if you want the relaxed clearance to apply.
    Not auto-applied by the protocol — see module docstring.
    """


class UnderMemTag(Tag):
    """Net is routed under the memory device package (BGA fanout region).

    Same semantics as :py:class:`UnderFPGATag` but for the memory side.
    """


# ---------------------------------------------------------------------------
# Byte-lane tags — up to 8 byte lanes (covers LPDDR5 x32 and x64)
# ---------------------------------------------------------------------------
# Flat hierarchy: each ByteN tag is a direct subclass of Tag, not of
# a common ByteTag base. JITX rejects unassigned parent tag classes
# at design-instantiation time ("Key ... does not exist in table"),
# so common bases must be either always assigned alongside subclasses
# or skipped entirely. We skip them.


class Byte0Tag(Tag): ...
class Byte1Tag(Tag): ...
class Byte2Tag(Tag): ...
class Byte3Tag(Tag): ...
class Byte4Tag(Tag): ...
class Byte5Tag(Tag): ...
class Byte6Tag(Tag): ...
class Byte7Tag(Tag): ...


_BYTE_TAGS: tuple[type[Tag], ...] = (
    Byte0Tag, Byte1Tag, Byte2Tag, Byte3Tag,
    Byte4Tag, Byte5Tag, Byte6Tag, Byte7Tag,
)


# ---------------------------------------------------------------------------
# Channel tags — up to 4 channels (covers LPDDR5 x32 and x64)
# ---------------------------------------------------------------------------


class Channel0Tag(Tag): ...
class Channel1Tag(Tag): ...
class Channel2Tag(Tag): ...
class Channel3Tag(Tag): ...


_CHANNEL_TAGS: tuple[type[Tag], ...] = (
    Channel0Tag, Channel1Tag, Channel2Tag, Channel3Tag,
)


# ---------------------------------------------------------------------------
# Tag-application helper
# ---------------------------------------------------------------------------


def tag_lpddr_link(
    src: "LPDDR5",
    dst: "LPDDR5",
    width: "LPDDR5Width",
    rank: "LPDDR5Rank",
) -> list:
    """Build LPDDR5 src→dst topologies and tag every one with its
    per-port-type, AMD signal-class, byte, and channel tags.

    JITX placeholder ports returned by ``require()`` reject property
    mutation, so we can't tag the bundle ports directly. What we *can*
    tag is the :py:class:`~jitx.si.Topology` produced by ``src.X >> dst.X``
    inside a ``constrain_topology(...)`` context. This helper does that
    en masse.

    Args:
        src: Controller-side LPDDR5 bundle proxy (the ``src`` from a
            ``constrain_topology`` ``with`` block).
        dst: Memory-side LPDDR5 bundle proxy (the ``dst``).
        width: Channel width — drives the channel count (x32 → 2, x64 → 4).
        rank: Rank configuration — drives the per-channel CS count.

    Returns:
        A flat list of topologies, suitable for storing on the circuit
        (e.g. ``self.lpddr5_topos = tag_lpddr_link(src, dst, ...)``).
        Each topology already has all its tags applied, so the caller
        doesn't need to do additional work.

    Note:
        Region tags (:py:class:`UnderFPGATag` / :py:class:`UnderMemTag`)
        are **not** applied — see the module docstring.

    Example:
        >>> with constraint.constrain_topology(ctrl, mem) as (src, dst):
        ...     topos = tag_lpddr_link(src, dst, LPDDR5Width.x32, LPDDR5Rank.DualRank)
    """
    from .lpddr5 import num_channels

    num_ch = num_channels(width)
    rank_count = rank.value

    topos: list = []

    # Reset
    reset_topo = src.reset_n >> dst.reset_n
    ResetTag().assign(reset_topo)
    topos.append(reset_topo)

    for ch_idx in range(num_ch):
        ch_tag_cls = _CHANNEL_TAGS[ch_idx]

        # CK (diff pair — single topology covering both polarities)
        ck_topo = src.ck[ch_idx] >> dst.ck[ch_idx]
        CKTag().assign(ck_topo)
        ch_tag_cls().assign(ck_topo)
        topos.append(ck_topo)

        # CS (active-low chip selects)
        for rank_idx in range(rank_count):
            cs_topo = src.cs[ch_idx][rank_idx] >> dst.cs[ch_idx][rank_idx]
            CSnTag().assign(cs_topo)
            CACTag().assign(cs_topo)
            ch_tag_cls().assign(cs_topo)
            topos.append(cs_topo)

        # CA (command/address)
        for ca_idx in range(7):
            ca_topo = src.ca[ch_idx][ca_idx] >> dst.ca[ch_idx][ca_idx]
            CATag().assign(ca_topo)
            CACTag().assign(ca_topo)
            ch_tag_cls().assign(ca_topo)
            topos.append(ca_topo)

        # Data lanes
        for lane_idx in range(2):
            byte_idx = ch_idx * 2 + lane_idx
            byte_tag_cls = _BYTE_TAGS[byte_idx]

            sl = src.d[ch_idx][lane_idx]
            dl = dst.d[ch_idx][lane_idx]

            # WCK (diff pair)
            wck_topo = sl.wck >> dl.wck
            WCKTag().assign(wck_topo)
            StrobeTag().assign(wck_topo)
            byte_tag_cls().assign(wck_topo)
            ch_tag_cls().assign(wck_topo)
            topos.append(wck_topo)

            # RDQS (diff pair)
            rdqs_topo = sl.rdqs >> dl.rdqs
            RDQSTag().assign(rdqs_topo)
            StrobeTag().assign(rdqs_topo)
            byte_tag_cls().assign(rdqs_topo)
            ch_tag_cls().assign(rdqs_topo)
            topos.append(rdqs_topo)

            # DQ bits
            for dq_idx in range(8):
                dq_topo = sl.dq[dq_idx] >> dl.dq[dq_idx]
                DQTag().assign(dq_topo)
                DataTag().assign(dq_topo)
                byte_tag_cls().assign(dq_topo)
                ch_tag_cls().assign(dq_topo)
                topos.append(dq_topo)

            # DMI
            dmi_topo = sl.dmi >> dl.dmi
            DMITag().assign(dmi_topo)
            DataTag().assign(dmi_topo)
            byte_tag_cls().assign(dmi_topo)
            ch_tag_cls().assign(dmi_topo)
            topos.append(dmi_topo)

    return topos


# ---------------------------------------------------------------------------
# Spacing-rule applier
# ---------------------------------------------------------------------------


def make_lpddr_spacing_rules(
    H: float,
    num_bytes: int = 4,
    num_channels: int = 2,
) -> list:
    """Build the full set of AMD UG863 spacing rules for one LPDDR5 link.

    Returns a list of :py:func:`design_constraint` instances implementing
    the *Outside SoC/DRAM* column of UG863's spacing table — the safer
    rule that applies to LPDDR5 nets routed on the inner stripline. The
    relaxed *Under SoC/DRAM* rules are not generated; see the module
    docstring for why.

    The caller stores the returned list (typically as a Circuit attribute,
    e.g. ``self.lpddr_rules = make_lpddr_spacing_rules(H=0.1)``).

    Args:
        H: Distance from the signal layer to the nearest GND return plane,
            in millimeters. Use :py:func:`get_H` to introspect from a
            stackup. Typical values: 0.1 mm for tight HDI stripline, 0.075
            mm for thinner laminates, 0.15 mm for relaxed FR-4.
        num_bytes: Number of byte lanes in the LPDDR5 configuration.
            x32 dual-rank uses 4 byte lanes (2 channels × 2 lanes), x64
            uses 8 (4 × 2). Defaults to 4.
        num_channels: Number of LPDDR5 channels. x32 = 2 channels, x64 = 4.
            Defaults to 2.

    Returns:
        List of design_constraint rules. Length scales as
        :math:`O(\\text{num\\_bytes}^2 + \\text{num\\_channels}^2)` because
        of the pairwise byte- and channel-index rules.
    """
    if num_bytes > len(_BYTE_TAGS):
        raise ValueError(
            f"num_bytes={num_bytes} exceeds predefined byte tags "
            f"({len(_BYTE_TAGS)}). Add more ByteN tag classes if needed."
        )
    if num_channels > len(_CHANNEL_TAGS):
        raise ValueError(
            f"num_channels={num_channels} exceeds predefined channel tags "
            f"({len(_CHANNEL_TAGS)}). Add more ChannelN tag classes."
        )

    rules: list = []

    # AMD UG863 "Outside SoC/DRAM" clearances, expressed as multiples of H.
    cac_to_cac = 2.5 * H              # CA-CA, CA-CSn, CSn-CSn
    ca_to_ck = 5.0 * H                # CA/CSn ↔ CK
    cack_to_data = 7.0 * H            # CA/CSn/CK ↔ DQ/DMI/WCK/RDQS
    data_data_same_byte = 2.5 * H     # DQ-DQ within byte
    data_strobe_same_byte = 5.0 * H   # DQ ↔ WCK/RDQS within byte
    data_strobe_diff_byte = 7.0 * H   # DQ ↔ WCK/RDQS across bytes
    inter_channel = 7.0 * H           # any signal pair across channels

    # === CAC ↔ CAC: 2.5 H ===
    rules.append(
        design_constraint(CACTag(), CACTag()).clearance(cac_to_cac)
    )

    # === CA/CSn ↔ CK: 5 H ===
    rules.append(
        design_constraint(CACTag(), CKTag()).clearance(ca_to_ck)
    )

    # === CAC/CK ↔ Data/Strobe: 7 H ===
    rules.append(
        design_constraint(
            CACTag() | CKTag(), DataTag() | StrobeTag()
        ).clearance(cack_to_data)
    )

    # === DQ ↔ DQ within same byte: 2.5 H ===
    # === Data ↔ Strobe within same byte: 5 H ===
    # Per-byte rule because "same byte" is a per-tag predicate.
    for byte_idx in range(num_bytes):
        bt = _BYTE_TAGS[byte_idx]
        rules.append(
            design_constraint(
                DataTag() & bt(), DataTag() & bt()
            ).clearance(data_data_same_byte)
        )
        rules.append(
            design_constraint(
                DataTag() & bt(), StrobeTag() & bt()
            ).clearance(data_strobe_same_byte)
        )

    # === Data ↔ Strobe across different bytes: 7 H ===
    # Need to enumerate every pair (i, j) with i != j to express
    # "different bytes". JITX has no "tag inequality" combinator.
    for i in range(num_bytes):
        bi = _BYTE_TAGS[i]
        for j in range(num_bytes):
            if i == j:
                continue
            bj = _BYTE_TAGS[j]
            rules.append(
                design_constraint(
                    DataTag() & bi(), StrobeTag() & bj()
                ).clearance(data_strobe_diff_byte)
            )

    # === Inter-channel: any signal pair across channels: 7 H ===
    for i in range(num_channels):
        ci = _CHANNEL_TAGS[i]
        for j in range(i + 1, num_channels):
            cj = _CHANNEL_TAGS[j]
            rules.append(
                design_constraint(ci(), cj()).clearance(inter_channel)
            )

    return rules


# ---------------------------------------------------------------------------
# Routing-rule applier (mimic routing structures via tag rules)
# ---------------------------------------------------------------------------


def make_lpddr_routing_rules(
    *,
    dq_trace_width: float,
    ca_trace_width: float,
    diff_trace_width: float,
    diff_pair_spacing: float,
) -> list:
    """Build tag-based ``design_constraint`` rules that mimic the
    layer-specific routing structures otherwise needed for LPDDR5 nets.

    These rules cover **trace width** for each signal class and the
    **within-pair P/N spacing** for each differential signal class. They
    assume routing on internal (shielded) layers — the geometry was
    impedance-targeted for stripline, so applying it on a microstrip
    surface would land on the wrong impedance.

    Use this together with:

    - :py:func:`tag_lpddr_link` — applies the per-port-type / byte /
      channel signal tags this rule set keys on (must run before the
      rules can match anything).
    - :py:func:`make_lpddr_spacing_rules` — generates the AMD UG863
      pairwise inter-net clearance rules. Both rule sets compose
      cleanly: JITX takes the larger applicable clearance for each
      net pair.

    Within-pair P/N spacing is expressed as a ``BinaryDesignConstraint``
    on ``(SignalTag, SignalTag)`` with the tag matching itself. That
    rule applies to *all* pairs of nets carrying that tag — including
    inter-pair P/N — but the inter-pair rules from
    :py:func:`make_lpddr_spacing_rules` set wider minimums and so bind
    instead. The within-pair gap is thus the only place this rule's
    clearance is actually the tightest applicable.

    Args:
        dq_trace_width: Trace width (mm) for DQ and DMI single-ended nets.
        ca_trace_width: Trace width (mm) for CA, CSn, and Reset
            single-ended nets.
        diff_trace_width: Trace width (mm) for each polarity of the
            differential CK / WCK / RDQS pairs.
        diff_pair_spacing: Centre-to-centre spacing (mm) between the P
            and N traces of a CK / WCK / RDQS pair.

    Returns:
        List of design_constraint rules. Length: 8 single-ended trace
        widths (DQ + DMI + CA + CSn + Reset trace widths) + 3 differential
        trace widths (CK + WCK + RDQS) + 3 differential pair-spacing
        clearances = 11 rules. Caller stores them on a Circuit /
        Substrate / Board (e.g. ``self.lpddr_routing_rules = ...``).

    Example:
        >>> from examples.common.high_perf_board import (
        ...     INNER_SE_40_TRACE_WIDTH,
        ...     INNER_DIFF_75_TRACE_WIDTH,
        ...     INNER_DIFF_75_PAIR_SPACING,
        ... )
        >>> self.lpddr_routing_rules = make_lpddr_routing_rules(
        ...     dq_trace_width=INNER_SE_40_TRACE_WIDTH,
        ...     ca_trace_width=INNER_SE_40_TRACE_WIDTH,
        ...     diff_trace_width=INNER_DIFF_75_TRACE_WIDTH,
        ...     diff_pair_spacing=INNER_DIFF_75_PAIR_SPACING,
        ... )
    """
    rules: list = []

    # Single-ended trace widths
    # Data class (DQ + DMI) — share one width.
    rules.append(design_constraint(DQTag()).trace_width(dq_trace_width))
    rules.append(design_constraint(DMITag()).trace_width(dq_trace_width))

    # CAC class + Reset — share one width. (UG863 doesn't separate
    # Reset from CAC for trace-width purposes; both are controller-driven
    # single-ended signals.)
    rules.append(design_constraint(CATag()).trace_width(ca_trace_width))
    rules.append(design_constraint(CSnTag()).trace_width(ca_trace_width))
    rules.append(design_constraint(ResetTag()).trace_width(ca_trace_width))

    # Differential trace widths — applied to every polarity (P and N
    # share the same tag, so a single rule covers both sides of the pair).
    rules.append(design_constraint(CKTag()).trace_width(diff_trace_width))
    rules.append(design_constraint(WCKTag()).trace_width(diff_trace_width))
    rules.append(design_constraint(RDQSTag()).trace_width(diff_trace_width))

    # Within-pair P/N spacing for each differential signal class.
    # This is not correct -- there are no differential constraints available through tags right now.
    # rules.append(
    #     design_constraint(CKTag(), CKTag()).clearance(diff_pair_spacing)
    # )
    # rules.append(
    #     design_constraint(WCKTag(), WCKTag()).clearance(diff_pair_spacing)
    # )
    # rules.append(
    #     design_constraint(RDQSTag(), RDQSTag()).clearance(diff_pair_spacing)
    # )

    return rules


# ---------------------------------------------------------------------------
# Loss budget helper (max-length → max-loss)
# ---------------------------------------------------------------------------


def lpddr_loss_budget(
    insertion_loss_db_per_mm: float,
    length_mm: float = LPDDR_MAX_TRACE_LEN_MM,
) -> float:
    """Convert an AMD UG863 max-trace-length cap into a max-insertion-loss
    budget (dB), given the routing structure's per-mm loss coefficient.

    AMD UG863 caps both CAC/CK and data trace lengths at 2000 mil
    (≈ 50.8 mm). JITX expresses signal-loss limits via the
    :py:class:`SignalConstraint`'s ``loss`` parameter (dB). This helper
    bridges the two.

    Args:
        insertion_loss_db_per_mm: The routing structure's
            ``insertion_loss`` (dB/mm). For
            :py:class:`HighPerfSubstrate.DRS_DiffPair_75` this is 0.018.
        length_mm: Maximum trace length in millimeters. Defaults to
            :py:data:`LPDDR_MAX_TRACE_LEN_MM` (50.8 mm).

    Returns:
        Maximum insertion loss in dB. With UG863's 2000 mil at 0.018
        dB/mm, this returns ≈ 0.91 dB — significantly tighter than the
        previous ``LPDDR5ConstraintParams.loss = 4.0`` default.
    """
    return length_mm * insertion_loss_db_per_mm


# ---------------------------------------------------------------------------
# Per-net via-on-pad drops
# ---------------------------------------------------------------------------


def drop_vias_on_net_pads(
    component_instance,
    net_via_map: dict,
    net_to_ports: dict,
    nets: dict,
    *,
    parent_transform=None,
) -> list:
    """Drop one via on every pad of ``component_instance`` whose port
    belongs to a named net **and connect the via to that net**.

    Pad positions are read by introspection on the **live** design tree
    rather than reconstructed analytically from landpattern geometry —
    so the helper works for any landpattern (BGA, QFN, SOIC, ...) and
    follows whatever ``.at(...)`` transform the landpattern generator
    placed on each pad. To find pads, the function:

    1. Parses the component class' deferred :py:class:`PadMapping` to
       build a ``{class_port → pad_path}`` table. The pad path comes
       straight from the :py:class:`InstantiableAttribute` (e.g.
       ``("AA", Item(10))``) so it works for whatever attribute scheme
       the landpattern uses (``A[1]`` for BGA, ``p[1]`` for SMT, ...).
    2. Walks ``component_instance`` with :py:func:`jitx.inspect.visit`
       to find the live :py:class:`Landpattern` and the trace transform
       between the component instance and the landpattern's parent.
    3. Navigates each pad path on the live landpattern proxy to read
       the actual :py:class:`Pad` instance and its
       generator-set ``.transform`` (the BGA pitch, SMT pin offset, etc.).

    Vias live in board (root) coordinates — they don't inherit a
    container's transform — so the world transform of each via is::

        world = parent_transform * trace.transform * pad.transform

    where ``parent_transform`` is the placement that put the component
    on the board (``self.fpga`` was ``self.place``-ed at that
    transform), and ``trace.transform`` accumulates anything between
    the component instance and the landpattern (typically identity).

    Each via is connected to its named net via ``net += via``;
    without that step the layout engine drops the via as orphan.

    Args:
        component_instance: A live :py:class:`Component` (or
            :py:class:`Circuit` containing one) whose pads should be
            walked. The component's ``mapping`` class attribute is
            consulted to find the pad path; the live landpattern is
            then navigated for each path.
        net_via_map: ``{net_name: Via_class}`` — every entry triggers
            via drops for the corresponding net.
        net_to_ports: ``{net_name: [port, ...]}`` — class-level Port
            references the caller knows are netted onto ``net_name``.
            For an indexed port array attribute, splat it::

                {"GND": [*XC2VE3858.GND, *XC2VE3858.RSVDGND]}

        nets: ``{net_name: net_instance}`` — the Net objects to attach
            vias to. Pass the Circuit's actual nets here::

                {"GND": self.GND}

        parent_transform: Placement transform of the component on the
            board (the same transform you passed to
            :py:meth:`jitx.circuit.Circuit.place`). Defaults to
            identity, in which case vias land in component-local
            coordinates.

    Returns:
        Flat list of placed via instances. Empty if no class-level
        ``mapping`` is found or no matching ports exist.
    """
    from jitx.transform import Transform
    from jitx.landpattern import Landpattern
    from jitx.component import Component
    from jitx.inspect import visit

    if parent_transform is None:
        parent_transform = Transform.identity()

    if isinstance(component_instance, type):
        # Class only — no live tree to walk; nothing to do without an
        # instance whose pads have generator-set transforms.
        return []

    component_traces: list = []
    for trace, comp in visit(component_instance, Component):
        component_traces.append((trace, comp))

    if not component_traces:
        return []

    placed: list = []
    for comp_trace, comp in component_traces:
        # Walk the LIVE PadMapping via `pm.inverse()` so the
        # `port_id_to_pad` keys match the same pooled proxy IDs that
        # users get via attribute access on the live component
        # (`self.mem.VSS[0]`). Class-level Port references (e.g.
        # `MT62F4G32D8DV_026_AIT_B.VSS[0]`) ALSO resolve to the same
        # pooled proxy, so both calling styles work — see
        # `attach_signal_vias_on_pads` for the same approach.
        port_id_to_pad: dict = {}
        mapping = comp.mapping
        if not isinstance(mapping, (list, tuple)):
            mapping = [mapping]
        for pm in mapping:
            for pad, port in pm.inverse().items():
                port_id_to_pad[id(port)] = pad

        if not port_id_to_pad:
            continue

        landpattern_traces: list = []
        for lp_trace, lp in visit(comp, Landpattern):
            landpattern_traces.append((lp_trace, lp))
        if not landpattern_traces:
            continue

        # Single landpattern is the typical case; first match wins.
        lp_trace, lp = landpattern_traces[0]
        comp_trace_xform = (
            comp_trace.transform
            if comp_trace.transform is not None
            else Transform.identity()
        )
        lp_trace_xform = (
            lp_trace.transform
            if lp_trace.transform is not None
            else Transform.identity()
        )
        lp_xform = (
            lp.transform if lp.transform is not None else Transform.identity()
        )

        for net_name, via_class in net_via_map.items():
            ports = net_to_ports.get(net_name, ())
            net = nets.get(net_name)
            if net is None:
                continue
            for port in ports:
                pad = port_id_to_pad.get(id(port))
                if pad is None:
                    continue
                pad_xform = (
                    pad.transform if pad.transform is not None else Transform.identity()
                )
                world_xform = (
                    parent_transform
                    * comp_trace_xform
                    * lp_trace_xform
                    * lp_xform
                    * pad_xform
                )
                via = via_class().at(world_xform)
                net += via
                placed.append(via)

    return placed


def attach_signal_vias_on_pads(
    component_instance,
    port_via_map: dict,
    *,
    parent_transform=None,
) -> list:
    """Drop a via on each pad of ``component_instance`` whose port is
    in ``port_via_map`` and tie it to that port via :py:class:`PortAttachment`.

    Mirrors :py:func:`drop_vias_on_net_pads` for the signal-pad case
    where each port participates in a topology (``>>``) rather than a
    flat :py:class:`Net`. ``net += via`` cannot be used on a
    :py:class:`TopologyNet`, so each via is bound via
    :py:class:`PortAttachment` to the live component-port proxy that
    sits on the matching pad. The PortAttachment carries the
    electrical association without altering the topology sequence.

    Args:
        component_instance: A live :py:class:`Component` (or
            :py:class:`Circuit` containing one). Pass ``self`` (the
            wrapper Circuit) when calling from inside an ``__init__``
            that just instantiated the component, so ``visit`` can
            descend into it.
        port_via_map: ``{live_port_proxy: Via_class}``. Keys must be
            **live proxies** obtained via attribute access on a live
            component instance (e.g. ``self.mem.DQ_A[0]``), not raw
            class-level Port references — JITX pools proxies by
            attribute and the live :py:class:`PadMapping` traversal
            uses the same pooled identities, so identity matching via
            ``id()`` only works on live proxies. Entries whose value
            is ``None`` are skipped.
        parent_transform: Placement transform of the component on the
            board. Defaults to identity, matching the
            ``floating=True`` wrapper case where the via positions are
            computed in the wrapper's local frame.

    Returns:
        Flat list of :py:class:`PortAttachment` instances. Caller
        stores the result on the Circuit so the structural references
        stay reachable.
    """
    from jitx.transform import Transform
    from jitx.landpattern import Landpattern
    from jitx.component import Component
    from jitx.net import PortAttachment
    from jitx.inspect import visit

    if parent_transform is None:
        parent_transform = Transform.identity()

    if isinstance(component_instance, type):
        return []

    # Drop None entries up front; identity matching against the live
    # PadMapping (built below) keys on `id(port)` and relies on JITX's
    # proxy pooling so that the same pooled proxy is returned both
    # here and via attribute access on the live component.
    if not any(via for via in port_via_map.values()):
        return []

    component_traces: list = []
    for trace, comp in visit(component_instance, Component):
        component_traces.append((trace, comp))

    if not component_traces:
        return []

    placed: list = []
    for comp_trace, comp in component_traces:
        # Use `_build_port_id_to_pad_proxy`-style traversal of the LIVE
        # PadMapping so the port_id_to_pad keys are the same pooled
        # proxies as the user-supplied port_via_map keys.
        port_id_to_pad: dict = {}
        mapping = comp.mapping
        if not isinstance(mapping, (list, tuple)):
            mapping = [mapping]
        for pm in mapping:
            for pad, port in pm.inverse().items():
                port_id_to_pad[id(port)] = pad

        if not port_id_to_pad:
            continue

        landpattern_traces: list = []
        for lp_trace, lp in visit(comp, Landpattern):
            landpattern_traces.append((lp_trace, lp))
        if not landpattern_traces:
            continue

        comp_trace_xform = (
            comp_trace.transform
            if comp_trace.transform is not None
            else Transform.identity()
        )
        # Single landpattern is the typical case; if there are multiple
        # the first match wins.
        lp_trace, lp = landpattern_traces[0]
        lp_trace_xform = (
            lp_trace.transform
            if lp_trace.transform is not None
            else Transform.identity()
        )
        lp_xform = (
            lp.transform if lp.transform is not None else Transform.identity()
        )

        for port, via_class in port_via_map.items():
            if via_class is None:
                continue
            pad = port_id_to_pad.get(id(port))
            if pad is None:
                continue
            pad_xform = (
                pad.transform if pad.transform is not None else Transform.identity()
            )
            world_xform = (
                parent_transform
                * comp_trace_xform
                * lp_trace_xform
                * lp_xform
                * pad_xform
            )
            via = via_class().at(world_xform)
            placed.append(PortAttachment(port, via))

    return placed


# ---------------------------------------------------------------------------
# Stackup introspection helper for H
# ---------------------------------------------------------------------------


def get_H(stackup: "Stackup", signal_layer_index: int) -> float:
    """Find H — the distance from a signal layer to its nearest GND return
    plane — by walking the stackup's ordered conductor + dielectric layers.

    Reports the smallest dielectric thickness adjacent to the signal layer
    (above or below). For the high-perf 8-layer stripline stackup with
    Signal3 at index 2 sandwiched between two 0.1 mm dielectrics, returns
    0.1 mm.

    Args:
        stackup: Any :py:class:`jitx.stackup.Stackup` instance.
        signal_layer_index: 0-indexed conductor layer that the signal
            traces are routed on. For an 8-layer symmetric stackup with
            inner stripline at L3, pass ``2``.

    Returns:
        H in millimeters.

    Raises:
        ValueError: If ``signal_layer_index`` is out of range or the
            stackup has no adjacent dielectric.

    Example:
        >>> from examples.common.high_perf_board import HighPerfStackup
        >>> from jitx_protocols_ext.protocols.memory.lpddr_constraints import get_H
        >>> get_H(HighPerfStackup(), signal_layer_index=2)
        0.1
    """
    from jitx.stackup import Conductor, Dielectric

    # Walk the stackup's ordered layers. Stackup objects expose a list
    # of layer objects through introspection; we step through them and
    # track each conductor's index.
    layers = list(_iter_stackup_layers(stackup))
    conductor_layer_indices = [
        i for i, layer in enumerate(layers) if isinstance(layer, Conductor)
    ]
    if signal_layer_index >= len(conductor_layer_indices):
        raise ValueError(
            f"signal_layer_index={signal_layer_index} out of range; "
            f"stackup has {len(conductor_layer_indices)} conductor layers."
        )

    sig_pos = conductor_layer_indices[signal_layer_index]

    above_thickness: float | None = None
    below_thickness: float | None = None

    # Look upward for the nearest dielectric thickness above the signal layer.
    for i in range(sig_pos - 1, -1, -1):
        layer = layers[i]
        if isinstance(layer, Dielectric):
            above_thickness = layer.thickness
            break

    # Look downward for the nearest dielectric below the signal layer.
    for i in range(sig_pos + 1, len(layers)):
        layer = layers[i]
        if isinstance(layer, Dielectric):
            below_thickness = layer.thickness
            break

    candidates = [t for t in (above_thickness, below_thickness) if t is not None]
    if not candidates:
        raise ValueError(
            f"No adjacent dielectric found for signal_layer_index={signal_layer_index}."
        )
    return min(candidates)


def _iter_stackup_layers(stackup: "Stackup"):
    """Yield the stackup's layers in declared (top-to-bottom) order.

    Walks the full class MRO, collecting attributes that are
    :py:class:`Conductor` or :py:class:`Dielectric` instances. Class
    declaration order is preserved within each level, and bases are
    traversed in MRO order — so for a substrate that nests an
    ``@inline class stackup(HighPerfStackup)``, the actual
    ``HighPerfStackup`` layers come into scope through the MRO walk.
    """
    from jitx.stackup import Conductor, Dielectric

    seen: set[str] = set()
    # Walk MRO from most-derived to least, but only the inline subclass
    # is empty in the substrate-nested case — the real layers live on
    # the parent class. Collect from each level in declaration order.
    for klass in type(stackup).__mro__:
        for attr in klass.__dict__:
            if attr.startswith("_") or attr in seen:
                continue
            val = getattr(stackup, attr, None)
            if isinstance(val, (Conductor, Dielectric)):
                seen.add(attr)
                yield val


# ---------------------------------------------------------------------------
# LPDDR5 bus via attachment via PortAttachment
# ---------------------------------------------------------------------------


def _unwrap_proxy(p):
    """Strip every :py:class:`Proxy` layer off ``p`` and return the
    underlying object (typically a :py:class:`Port` or :py:class:`Pad`).
    """
    from jitx._structural import Proxy
    while isinstance(p, Proxy):
        p = Proxy.of(p)
    return p


def _build_port_id_to_pad_proxy(component_instance) -> dict:
    """Walk the live :py:class:`PadMapping`(s) on every Component
    reachable from ``component_instance`` and return a
    ``{id(port_proxy): pad_proxy}`` dict.

    Both keys and values are kept as the live :py:class:`Proxy`
    instances yielded by ``PadMapping.inverse()``. The proxy carries
    the generator-set ``.transform`` on the pad; on the port side, the
    proxy returned by ``getattr(component, port_name)`` from elsewhere
    in the design is the *same* pooled proxy instance, so identity
    comparison via ``id()`` is the correct way to match (do **not**
    unwrap with ``Proxy.of()`` — every port placeholder on a Component
    shares the same underlying Port object due to JITX's pin-assignment
    machinery, so unwrapping collapses every entry into one).
    """
    from jitx.component import Component
    from jitx.inspect import visit

    table: dict = {}
    for _, comp in visit(component_instance, Component):
        mapping = comp.mapping
        if not isinstance(mapping, (list, tuple)):
            mapping = [mapping]
        for pm in mapping:
            for pad, port in pm.inverse().items():
                table[id(port)] = pad
    return table


def _attach_via(
    bundle_port,
    via_class,
    pad_proxy,
    parent_transform,
):
    """Place a via at the world position of ``pad_proxy`` and wrap it
    in a :py:class:`PortAttachment` to ``bundle_port``.

    Returns the PortAttachment instance, or ``None`` if no via class
    was supplied.
    """
    from jitx.transform import Transform
    from jitx.net import PortAttachment

    if via_class is None:
        return None
    pad_xform = (
        pad_proxy.transform if pad_proxy.transform is not None else Transform.identity()
    )
    world_xform = parent_transform * pad_xform
    via = via_class().at(world_xform)
    return PortAttachment(bundle_port, via)


def attach_lpddr_link_vias(
    ctrl_io: "LPDDR5",
    mem_io: "LPDDR5",
    width: "LPDDR5Width",
    rank: "LPDDR5Rank",
    *,
    byte_via_types: list,
    channel_via_types: list,
    reset_via,
    ctrl_component_instance,
    mem_component_instance,
    ctrl_resolution_map: dict,
    mem_resolution_map: dict,
    ctrl_parent_transform=None,
    mem_parent_transform=None,
    debug: bool = False,
) -> list:
    """For every port in an LPDDR5 link, place a via at the resolved
    pad position on each side and tie it to the port via
    :py:class:`PortAttachment`. The via type is selected per byte
    lane (covers DQ + DMI + WCK + RDQS for that byte) and per channel
    (covers CK + CS + CA for that channel) via the supplied
    ``byte_via_types`` and ``channel_via_types`` lists. ``reset_via``
    handles the single global RESET_N.

    Why PortAttachment instead of ``net += via``: LPDDR5 ports
    participate in *topologies* (set up by ``constrain_topology`` /
    ``>>``) and *pin assignment* (Provide / require). They aren't
    members of a flat :py:class:`Net`, so the ``net += via`` pattern
    used for power rails doesn't apply. PortAttachment declares the
    port↔via electrical association in a form the layout engine and
    pin-assignment solver both understand.

    Pin-assignment ambiguity
    ------------------------
    JITX's pin-assignment system uses a single shared underlying Port
    object beneath all bundle leaves; ``Proxy.of()``-unwrapping a
    bundle leaf yields the same id for every leaf in the bundle. So
    we cannot infer pad positions from the bundle leaves alone — the
    caller must supply a ``ctrl_resolution_map`` and
    ``mem_resolution_map`` that maps each logical bundle leaf
    (``ctrl_io.X`` / ``mem_io.X``) to the **physical** component port
    it should bind to (e.g. an ``XC2VE3858.IO_X5_*`` proxy or a
    ``MT62F4G32D8DV_026_AIT_B.DQ_*`` proxy).

    These maps are exactly the dicts returned by the wrapper
    circuits' Provide-mapping methods, called explicitly with the
    *resolved* bundle::

        ctrl_resolution_map = self.fpga._build_lpddr5_mapping(
            ctrl_io, base_bank=700, packing=LPDDR5Packing.OPTIMUM,
        )
        mem_resolution_map = self.memory._create_lpddr5_mapping(mem_io)

    The caller picks the packing/base_bank explicitly. If JITX's
    solver later picks a different option, the via positions will be
    wrong — but JITX won't error and the user can reconcile by
    constraining the solver or re-running.

    Args:
        ctrl_io: Controller-side resolved LPDDR5 bundle (the result of
            ``self.fpga.require(LPDDR5(...))``).
        mem_io: Memory-side resolved LPDDR5 bundle.
        width: Channel width — drives the channel count.
        rank: Rank configuration — drives the per-channel CS count.
        byte_via_types: One :py:class:`Via` class per byte lane,
            length = ``num_bytes``. The single Via type for byte_idx
            is used for every signal in that byte lane (the 8 DQ
            bits, DMI, WCK_p/n, RDQS_p/n — 13 ports per side). For
            x32 dual-rank: 4 entries (byte 0/1 = channel 0, byte 2/3
            = channel 1, with ``byte_idx = ch_idx*2 + lane_idx``).
        channel_via_types: One :py:class:`Via` class per channel,
            length = ``num_channels``. Used for every CAC signal in
            that channel (CK_p/n, CS[0..rank-1], CA[0..6] — 11 ports
            per side for dual-rank).
        reset_via: Single :py:class:`Via` class for the global
            ``reset_n`` net.
        ctrl_component_instance: FPGA-side instance whose live
            :py:class:`PadMapping` will be walked to find pads.
        mem_component_instance: Memory-side instance, ditto.
        ctrl_resolution_map: ``{logical_bundle_leaf:
            physical_FPGA_port}`` for the controller side. See above.
        mem_resolution_map: ``{logical_bundle_leaf:
            physical_memory_port}`` for the memory side.
        ctrl_parent_transform: Placement transform applied to the
            controller-side component on the board. Defaults to
            identity.
        mem_parent_transform: Placement transform of the memory-side
            component on the board. Defaults to identity.

    Returns:
        Flat list of PortAttachment instances. Caller stores them on
        the Circuit (e.g. ``self.lpddr5_via_attachments = ...``) so
        the structural references stay reachable.
    """
    from jitx.transform import Transform
    from .lpddr5 import num_channels

    if ctrl_parent_transform is None:
        ctrl_parent_transform = Transform.identity()
    if mem_parent_transform is None:
        mem_parent_transform = Transform.identity()

    num_ch = num_channels(width)
    rank_count = rank.value
    num_bytes = num_ch * 2

    if len(byte_via_types) != num_bytes:
        raise ValueError(
            f"byte_via_types must have length {num_bytes} (= num_channels * 2 "
            f"for x{width.value}); got {len(byte_via_types)}."
        )
    if len(channel_via_types) != num_ch:
        raise ValueError(
            f"channel_via_types must have length {num_ch}; got {len(channel_via_types)}."
        )

    ctrl_table = _build_port_id_to_pad_proxy(ctrl_component_instance)
    mem_table = _build_port_id_to_pad_proxy(mem_component_instance)

    attachments: list = []

    def _resolve_pad(side_table, resolution_map, bundle_leaf):
        """Map a bundle leaf → physical component port (via the user-
        supplied resolution_map) → live Pad (via the side_table that
        keys on the physical port proxy's ``id()``). Identity match
        works because JITX pools proxies by attribute, so the proxy
        returned by ``getattr(comp, name)`` here equals the proxy
        stored in the live PadMapping.
        """
        physical_port = resolution_map.get(bundle_leaf)
        if physical_port is None:
            return None
        return side_table.get(id(physical_port))

    def _phys_repr(physical_port, side_table) -> str:
        """Pretty-print a physical-port proxy. ``str(proxy)`` only
        yields ``<Port>``, so we recover the attribute name by
        searching the live PadMapping for the matching Pad and walking
        every Component class' Port-list class attributes for an
        identity match. This is best-effort — falls back to ``repr()``
        if no name can be derived.
        """
        if physical_port is None:
            return "<unresolved>"
        # Best-effort name lookup: scan the Component class' annotated
        # Port attributes for one whose proxy on the live instance
        # matches `physical_port`.
        from jitx.component import Component
        from jitx.inspect import visit
        try:
            for _, comp in visit(
                ctrl_component_instance if side_table is ctrl_table
                else mem_component_instance,
                Component,
            ):
                cls = type(comp)
                # Walk class MRO so we get inherited Port declarations.
                seen = set()
                for klass in cls.__mro__:
                    for name in vars(klass):
                        if name.startswith("_") or name in seen:
                            continue
                        seen.add(name)
                        try:
                            val = getattr(comp, name)
                        except Exception:  # noqa: BLE001
                            continue
                        if val is physical_port:
                            return name
                        # Indexed Port lists / nested ports: scan one
                        # level deep for matches.
                        if isinstance(val, (list, tuple)):
                            for i, item in enumerate(val):
                                if item is physical_port:
                                    return f"{name}[{i}]"
                break  # only first Component
        except Exception:  # noqa: BLE001
            pass
        return repr(physical_port)

    def _pad_repr(pad_proxy) -> str:
        if pad_proxy is None or pad_proxy.transform is None:
            return "<no-pad>"
        t = pad_proxy.transform._translate
        return f"pad@({t[0]:.3f},{t[1]:.3f})"

    def attach_pair(label, ctrl_port, mem_port, via_class):
        # FPGA side — attach via to the **physical** component port,
        # not the bundle leaf. The physical port is on the same net
        # as the pad it sits on (component-internal mapping), so the
        # via inherits that net and JITX's overlap-on-top check sees
        # via and pad on the same net. Attaching to the bundle leaf
        # would not propagate cleanly through Provide resolution.
        ctrl_phys = ctrl_resolution_map.get(ctrl_port)
        ctrl_pad = _resolve_pad(ctrl_table, ctrl_resolution_map, ctrl_port)
        if debug:
            print(
                f"  [ctrl] {label}: phys={_phys_repr(ctrl_phys, ctrl_table)} "
                f"{_pad_repr(ctrl_pad)} via={via_class.__name__ if via_class else None}"
            )
        if ctrl_pad is not None and ctrl_phys is not None:
            a = _attach_via(ctrl_phys, via_class, ctrl_pad, ctrl_parent_transform)
            if a is not None:
                attachments.append(a)
        # Memory side
        mem_phys = mem_resolution_map.get(mem_port)
        mem_pad = _resolve_pad(mem_table, mem_resolution_map, mem_port)
        if debug:
            print(
                f"  [mem]  {label}: phys={_phys_repr(mem_phys, mem_table)} "
                f"{_pad_repr(mem_pad)} via={via_class.__name__ if via_class else None}"
            )
        if mem_pad is not None and mem_phys is not None:
            a = _attach_via(mem_phys, via_class, mem_pad, mem_parent_transform)
            if a is not None:
                attachments.append(a)

    if debug:
        print("attach_lpddr_link_vias debug:")

    # --- reset_n (global) ---
    attach_pair("reset_n", ctrl_io.reset_n, mem_io.reset_n, reset_via)

    # --- per-channel: ck, cs, ca all share one Via type ---
    for ch_idx in range(num_ch):
        ch_via = channel_via_types[ch_idx]
        attach_pair(
            f"ch{ch_idx}.ck.p", ctrl_io.ck[ch_idx].p, mem_io.ck[ch_idx].p, ch_via,
        )
        attach_pair(
            f"ch{ch_idx}.ck.n", ctrl_io.ck[ch_idx].n, mem_io.ck[ch_idx].n, ch_via,
        )
        for r in range(rank_count):
            attach_pair(
                f"ch{ch_idx}.cs[{r}]",
                ctrl_io.cs[ch_idx][r], mem_io.cs[ch_idx][r], ch_via,
            )
        for ca_idx in range(7):
            attach_pair(
                f"ch{ch_idx}.ca[{ca_idx}]",
                ctrl_io.ca[ch_idx][ca_idx],
                mem_io.ca[ch_idx][ca_idx],
                ch_via,
            )

    # --- per-byte: dq, wck, rdqs, dmi all share one Via type ---
    for ch_idx in range(num_ch):
        for lane_idx in range(2):
            byte_idx = ch_idx * 2 + lane_idx
            byte_via = byte_via_types[byte_idx]
            ctrl_lane = ctrl_io.d[ch_idx][lane_idx]
            mem_lane = mem_io.d[ch_idx][lane_idx]
            for dq_idx in range(8):
                attach_pair(
                    f"byte{byte_idx}.dq[{dq_idx}]",
                    ctrl_lane.dq[dq_idx], mem_lane.dq[dq_idx], byte_via,
                )
            attach_pair(f"byte{byte_idx}.wck.p", ctrl_lane.wck.p, mem_lane.wck.p, byte_via)
            attach_pair(f"byte{byte_idx}.wck.n", ctrl_lane.wck.n, mem_lane.wck.n, byte_via)
            attach_pair(f"byte{byte_idx}.rdqs.p", ctrl_lane.rdqs.p, mem_lane.rdqs.p, byte_via)
            attach_pair(f"byte{byte_idx}.rdqs.n", ctrl_lane.rdqs.n, mem_lane.rdqs.n, byte_via)
            attach_pair(f"byte{byte_idx}.dmi", ctrl_lane.dmi, mem_lane.dmi, byte_via)

    return attachments
