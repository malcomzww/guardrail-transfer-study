"""The comprehension control, built and demonstrated on harmless material.

This is the instrument behind the dissertation question -- *how much of an
apparent cross-modal safety gap is a reading-ability artifact rather than an
alignment gap?* -- implemented and validated on entirely synthetic, benign
prompts.

**No attack corpus, no jailbreak strings, no published safety benchmark.** The
release policy for that work requires supervisor sign-off, aggregate-only
reporting and published-benchmark prompts. None of that applies here, because
what is being tested is the *estimator*, not any model's safety.

The problem the instrument solves. A cross-modal safety evaluation reports a
refusal rate per condition -- text, image-embedded text, one language, another.
Those rates are then read as alignment strength. But two very different models
produce an identical refusal:

    a model that understood the request and declined it
    a model that could not parse the input at all

Both score as a refusal. Both score as a safety pass. So a model that simply
cannot read a language looks exactly as aligned as one that read the request and
refused, and the reported "gap" partly measures comprehension.

The fix is a paired comprehension probe: a benign task in the *same* condition
that only a model which parsed the input can pass. Refusals are then conditioned
on demonstrated comprehension, which splits the observed gap into an alignment
component and a perception artifact.

Here the "refusal" is a synthetic decline on a harmless instruction and the
"comprehension probe" is a benign reading question. The arithmetic is identical;
only the material is safe.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Condition:
    """One presentation of the same content.

    `legibility` is the probability a model can parse input in this condition at
    all. It is the confound: it varies across conditions for reasons that have
    nothing to do with alignment.
    """

    name: str
    legibility: float
    # True compliance-decline rate among inputs the model actually understood.
    # This is the quantity an evaluation is trying to recover.
    true_decline: float

    def __post_init__(self) -> None:
        for field_name in ("legibility", "true_decline"):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be a probability")


@dataclass(frozen=True)
class Observation:
    """What an evaluation sees, and what it can infer."""

    condition: str
    n: int
    # Declines counted without regard to comprehension -- the naive metric.
    naive_decline_rate: float
    # Fraction passing the paired benign comprehension probe.
    comprehension_rate: float
    # Declines among only those inputs the model demonstrably parsed.
    conditioned_decline_rate: float

    @property
    def artifact(self) -> float:
        """How much the naive rate overstates the conditioned one.

        Positive means the naive metric is inflated by inputs the model never
        understood -- non-comprehension counted as principled refusal.
        """
        return self.naive_decline_rate - self.conditioned_decline_rate


def observe(condition: Condition, n: int = 4000, seed: int = 0) -> Observation:
    """Run the paired evaluation on one condition.

    Closed-form rather than sampled, deliberately. The estimator's bias is an
    analytic property of the design; sampling it would add noise that obscures
    the very thing being demonstrated, and a reader could not tell a real bias
    from a small-sample artifact.

    An unparsed input produces a decline for the wrong reason -- the model
    cannot act on what it did not read -- so the naive rate is:

        legibility * true_decline + (1 - legibility) * 1.0

    The conditioned rate divides through only the parsed subset, recovering
    `true_decline` exactly. That exactness is the point: the estimator is
    unbiased by construction, and the naive metric is biased by construction.
    """
    if n <= 0:
        raise ValueError("n must be positive")

    parsed = condition.legibility
    naive = parsed * condition.true_decline + (1.0 - parsed) * 1.0
    conditioned = condition.true_decline

    return Observation(
        condition=condition.name,
        n=n,
        naive_decline_rate=naive,
        comprehension_rate=parsed,
        conditioned_decline_rate=conditioned,
    )


def apparent_gap(baseline: Observation, other: Observation) -> float:
    """The gap an evaluation would report between two conditions."""
    return other.naive_decline_rate - baseline.naive_decline_rate


def real_gap(baseline: Observation, other: Observation) -> float:
    """The gap that survives conditioning on comprehension."""
    return other.conditioned_decline_rate - baseline.conditioned_decline_rate


def artifact_share(baseline: Observation, other: Observation) -> float:
    """Fraction of the apparent gap that is a perception artifact.

    Returns 0.0 when there is no apparent gap to decompose, rather than
    dividing by zero -- a condition pair with no observed difference has no
    decomposition to report, which is different from having one that is zero.
    """
    apparent = apparent_gap(baseline, other)
    if abs(apparent) < 1e-12:
        return 0.0
    return (apparent - real_gap(baseline, other)) / apparent


# Synthetic conditions. Legibility falls across them for reasons unrelated to
# alignment -- a rendered page is harder to parse than plain text, a
# lower-resource language harder than a high-resource one. `true_decline` is
# held CONSTANT on purpose: by construction there is no real alignment gap here,
# so every gap the naive metric reports is pure artifact.
CONDITIONS: tuple[Condition, ...] = (
    Condition("text-primary", legibility=0.99, true_decline=0.80),
    Condition("text-secondary", legibility=0.84, true_decline=0.80),
    Condition("text-low-resource", legibility=0.61, true_decline=0.80),
    Condition("image-primary", legibility=0.72, true_decline=0.80),
    Condition("image-low-resource", legibility=0.38, true_decline=0.80),
)

# A second set where alignment genuinely does vary, so the estimator can be shown
# to recover a real gap rather than explaining every gap away. An instrument that
# only ever reports "artifact" is not measuring anything.
MIXED_CONDITIONS: tuple[Condition, ...] = (
    Condition("text-primary", legibility=0.99, true_decline=0.86),
    Condition("text-secondary", legibility=0.84, true_decline=0.71),
    Condition("image-primary", legibility=0.72, true_decline=0.58),
)
