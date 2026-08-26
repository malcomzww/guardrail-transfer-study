"""How many prompts the comprehension control actually needs.

The estimator in `instrument.py` is unbiased. That says nothing about whether a
study can afford to use it, because conditioning on comprehension **throws data
away**: in a condition where only 38% of inputs are parsed, a 400-prompt run
yields roughly 150 usable observations, and the interval around the conditioned
rate is correspondingly wide.

That is the practical objection to the whole method, and it deserves a number
rather than a hand-wave. This module computes it.

The trade the design faces:

    naive metric        every prompt contributes, and the estimate is biased
    conditioned metric  only parsed prompts contribute, and it is unbiased

Below some sample size the biased estimator is actually *closer* to the truth,
because its bias is smaller than the conditioned estimator's noise. Finding that
crossover is what tells you whether your study is large enough to bother
conditioning at all.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .instrument import Condition


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Wilson rather than the normal approximation, and the reason matters here:
    refusal rates in these studies sit near 0.8-0.95, where the normal interval
    routinely extends above 1.0 and produces a nonsensical upper bound. Wilson
    stays inside [0, 1] by construction and has better coverage in exactly that
    region.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= successes <= n:
        raise ValueError("successes must be between 0 and n")

    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    spread = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def interval_width(p: float, n: int, z: float = 1.96) -> float:
    """Width of the Wilson interval at a given proportion and sample size.

    Takes a proportion rather than a count so it can be evaluated at a
    hypothetical rate during planning, before any data exists.
    """
    if n <= 0:
        return 1.0
    lo, hi = wilson_interval(round(p * n), n, z)
    return hi - lo


@dataclass(frozen=True)
class PowerResult:
    """What one sample size buys in one condition."""

    condition: str
    prompts: int
    # Prompts surviving the comprehension filter.
    usable: int
    naive_width: float
    conditioned_width: float
    naive_bias: float

    @property
    def naive_total_error(self) -> float:
        """Bias plus half-width: how far the naive estimate can be from truth.

        Adding a systematic error to a random one is not statistically rigorous
        as a combined interval, but it is the right comparison for the decision
        being made -- which estimator lands closer to the answer.
        """
        return self.naive_bias + self.naive_width / 2

    @property
    def conditioned_total_error(self) -> float:
        """No bias, so only the half-width."""
        return self.conditioned_width / 2

    @property
    def conditioning_pays(self) -> bool:
        return self.conditioned_total_error < self.naive_total_error


def power_at(condition: Condition, prompts: int, z: float = 1.96) -> PowerResult:
    """Compare the two estimators at a given sample size.

    The naive estimator uses every prompt and carries a bias equal to
    `(1 - legibility) * (1 - true_decline)` -- the share of unparsed inputs
    times how much a decline-for-non-comprehension overstates the true rate.

    The conditioned estimator uses only the parsed subset, so its interval is
    wider by roughly 1/sqrt(legibility).
    """
    if prompts <= 0:
        raise ValueError("prompts must be positive")

    usable = max(1, round(prompts * condition.legibility))
    naive_rate = (
        condition.legibility * condition.true_decline
        + (1 - condition.legibility) * 1.0
    )

    return PowerResult(
        condition=condition.name,
        prompts=prompts,
        usable=usable,
        naive_width=interval_width(naive_rate, prompts, z),
        conditioned_width=interval_width(condition.true_decline, usable, z),
        naive_bias=naive_rate - condition.true_decline,
    )


def crossover_sample_size(
    condition: Condition, z: float = 1.96, max_prompts: int = 20_000
) -> int | None:
    """Smallest sample at which conditioning beats the naive estimator.

    Below this, the conditioned estimator's extra noise exceeds the naive
    estimator's bias and the biased number is closer to the truth. That is an
    uncomfortable but real result: **the control is not free, and a study too
    small to afford it is better off reporting the biased rate and saying so.**

    Returns None when conditioning never wins within the swept range -- which
    happens for a condition legible enough that the bias is negligible.
    """
    for prompts in range(20, max_prompts, 20):
        if power_at(condition, prompts, z).conditioning_pays:
            return prompts
    return None


def required_prompts_for_width(
    condition: Condition, target_width: float, z: float = 1.96,
    max_prompts: int = 100_000
) -> int | None:
    """Prompts needed for a conditioned interval no wider than `target_width`.

    The number a study proposal actually needs. Because only the parsed subset
    counts, this scales roughly as 1/legibility -- a condition at 38%
    comprehension needs about 2.6x the prompts of one at 99% for the same
    precision.
    """
    if not 0 < target_width < 1:
        raise ValueError("target_width must be in (0, 1)")

    for prompts in range(20, max_prompts, 20):
        if power_at(condition, prompts, z).conditioned_width <= target_width:
            return prompts
    return None


def detectable_gap(condition: Condition, prompts: int, z: float = 1.96) -> float:
    """Smallest alignment gap this sample could distinguish from zero.

    Approximated as the sum of two half-widths -- the baseline's and this
    condition's -- which is the standard conservative rule for whether two
    intervals overlap. A gap smaller than this is not reportable at this sample
    size, however suggestive the point estimate looks.
    """
    usable = max(1, round(prompts * condition.legibility))
    return interval_width(condition.true_decline, usable, z)
