"""The probe is an instrument too, and a bad one re-introduces the bias.

`instrument.py` assumes the comprehension probe is valid: that passing it means
the model parsed the input, and failing it means the model did not. That
assumption is doing all the work, and it is the part a reviewer should attack
first.

Two ways it fails, in opposite directions:

    probe too easy   a model that cannot parse the harmful request still passes
                     the benign probe, so unparsed inputs are admitted to the
                     conditioned set and the bias comes straight back

    probe too hard   a model that parsed the request fails the probe anyway, so
                     genuine observations are discarded -- unbiased but wasteful,
                     and it can flip to biased if difficulty correlates with
                     whatever the refusal depends on

The second is the subtler one. Discarding data at random costs precision. But if
the probe is harder in exactly the conditions where refusal is also harder, the
discarding is not random and the estimator is biased again -- by a mechanism the
first design was built to remove.

This module quantifies both, so the README can state how good the probe has to
be rather than assuming it is perfect.
"""

from __future__ import annotations

from dataclasses import dataclass

from .instrument import Condition


@dataclass(frozen=True)
class Probe:
    """A comprehension probe with stated error rates.

    `false_pass` is P(probe passes | model did not parse) -- the probe is too
    easy. `false_fail` is P(probe fails | model did parse) -- too hard.

    A perfect probe has both at zero, which is what `instrument.py` assumes.
    """

    name: str
    false_pass: float
    false_fail: float
    # Whether difficulty correlates with the conditions that lower legibility.
    # A probe that gets harder exactly where reading gets harder is the
    # dangerous case, because its errors stop being random.
    correlated: bool = False

    def __post_init__(self) -> None:
        for field_name in ("false_pass", "false_fail"):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be a probability")


@dataclass(frozen=True)
class ProbeResult:
    """What the estimator recovers with an imperfect probe."""

    condition: str
    probe: str
    true_decline: float
    estimated_decline: float
    admitted_fraction: float

    @property
    def residual_bias(self) -> float:
        """How much bias survives the correction.

        Zero means the probe did its job. Positive means unparsed inputs leaked
        into the conditioned set.
        """
        return self.estimated_decline - self.true_decline


def estimate_with_probe(
    condition: Condition, probe: Probe
) -> ProbeResult:
    """Conditioned decline rate when the probe itself makes errors.

    Four groups of inputs, and only the first should count:

        parsed,     probe passes   -> admitted, declines at true_decline
        parsed,     probe fails    -> discarded (false_fail), a precision cost
        unparsed,   probe passes   -> admitted (false_pass), declines at 1.0
        unparsed,   probe fails    -> discarded correctly

    A correlated probe is modelled as having its false-fail rate scale up as
    legibility falls: the harder the condition is to read, the more genuinely
    parsed inputs the probe wrongly rejects.
    """
    parsed = condition.legibility
    unparsed = 1.0 - parsed

    false_fail = probe.false_fail
    if probe.correlated:
        # Scales from the stated rate at perfect legibility to roughly double
        # it at zero legibility.
        false_fail = min(1.0, probe.false_fail * (2.0 - parsed))

    admitted_parsed = parsed * (1.0 - false_fail)
    admitted_unparsed = unparsed * probe.false_pass
    admitted = admitted_parsed + admitted_unparsed

    if admitted <= 0:
        # The probe rejected everything; no estimate is possible.
        return ProbeResult(
            condition=condition.name,
            probe=probe.name,
            true_decline=condition.true_decline,
            estimated_decline=float("nan"),
            admitted_fraction=0.0,
        )

    declines = admitted_parsed * condition.true_decline + admitted_unparsed * 1.0

    return ProbeResult(
        condition=condition.name,
        probe=probe.name,
        true_decline=condition.true_decline,
        estimated_decline=declines / admitted,
        admitted_fraction=admitted,
    )


def max_tolerable_false_pass(
    condition: Condition, tolerance: float, step: float = 0.005
) -> float:
    """Largest false-pass rate keeping residual bias within `tolerance`.

    The number a probe design has to hit. Reported per condition because the
    requirement is strictest exactly where legibility is lowest -- there are
    more unparsed inputs available to leak through.
    """
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")

    best = 0.0
    rate = 0.0
    while rate <= 1.0:
        probe = Probe("scan", false_pass=rate, false_fail=0.0)
        result = estimate_with_probe(condition, probe)
        if abs(result.residual_bias) > tolerance:
            break
        best = rate
        rate += step
    return best


# Four probe designs spanning the plausible range. The rates are stated
# parameters, not measurements -- what is being shown is how the estimator
# responds to probe quality, not how good any real probe is.
PROBES: tuple[Probe, ...] = (
    Probe("ideal", false_pass=0.00, false_fail=0.00),
    Probe("slightly-easy", false_pass=0.15, false_fail=0.02),
    Probe("too-easy", false_pass=0.45, false_fail=0.02),
    Probe("too-hard", false_pass=0.02, false_fail=0.25),
    Probe("correlated-hard", false_pass=0.02, false_fail=0.25, correlated=True),
)
