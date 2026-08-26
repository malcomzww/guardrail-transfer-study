"""Sample-size arithmetic behind the control.

The estimator being unbiased is worth nothing if a realistic study cannot afford
the data it discards. These check that the cost is computed correctly, including
the uncomfortable case where conditioning does not pay.
"""

from __future__ import annotations

import pytest

from guardrail_transfer_study.instrument import CONDITIONS, Condition
from guardrail_transfer_study.power import (
    crossover_sample_size,
    detectable_gap,
    interval_width,
    power_at,
    required_prompts_for_width,
    wilson_interval,
)


def test_wilson_interval_contains_the_point_estimate():
    for successes, n in ((5, 20), (80, 100), (1, 10), (99, 100)):
        lo, hi = wilson_interval(successes, n)
        assert lo <= successes / n <= hi


def test_wilson_interval_stays_inside_zero_one():
    """The reason Wilson is used rather than the normal approximation.

    Refusal rates in these studies sit near 0.8-0.95, where the normal interval
    routinely runs above 1.0 and produces an upper bound that cannot happen.
    """
    for successes, n in ((100, 100), (0, 100), (99, 100), (1, 100)):
        lo, hi = wilson_interval(successes, n)
        assert 0.0 <= lo <= hi <= 1.0


def test_interval_narrows_as_the_sample_grows():
    widths = [interval_width(0.8, n) for n in (20, 50, 100, 400, 1600)]
    for earlier, later in zip(widths, widths[1:], strict=False):
        assert later < earlier


def test_interval_is_widest_near_one_half():
    """Binomial variance peaks at p=0.5, so precision is cheapest at the extremes."""
    assert interval_width(0.5, 200) > interval_width(0.9, 200)
    assert interval_width(0.5, 200) > interval_width(0.1, 200)


def test_conditioning_discards_data_in_proportion_to_illegibility():
    """The cost of the method, stated rather than hidden."""
    for condition in CONDITIONS:
        result = power_at(condition, 1000)
        assert abs(result.usable - 1000 * condition.legibility) <= 1


def test_naive_bias_matches_its_closed_form():
    """(1 - legibility) * (1 - true_decline), derived here independently."""
    for condition in CONDITIONS:
        expected = (1 - condition.legibility) * (1 - condition.true_decline)
        assert abs(power_at(condition, 500).naive_bias - expected) < 1e-12


def test_bias_is_zero_when_everything_is_legible():
    clean = Condition("clean", legibility=1.0, true_decline=0.8)
    assert abs(power_at(clean, 500).naive_bias) < 1e-12


def test_conditioned_interval_is_wider_than_the_naive_one():
    """It uses fewer observations, so it must be less precise.

    This is the honest cost of the correction and the reason the crossover
    question is worth asking at all.
    """
    for condition in CONDITIONS:
        if condition.legibility >= 1.0:
            continue
        result = power_at(condition, 400)
        assert result.conditioned_width > result.naive_width


def test_conditioning_pays_where_the_bias_is_large():
    """At the sample sizes a real study uses, the bias dominates the noise."""
    for condition in CONDITIONS:
        if condition.legibility >= 0.95:
            continue
        assert power_at(condition, 400).conditioning_pays


def test_conditioning_is_free_when_there_is_nothing_to_correct():
    """The boundary case, and it is a tie rather than a loss.

    I expected the conditioned estimator to lose here -- a nearly-legible
    condition has almost no bias to remove, so the extra noise should dominate.
    It does not: at 99.9% legibility the discarded fraction rounds away entirely,
    so both estimators use the same sample and the widths are identical. The
    correction is free rather than harmful, which is a better result than the
    one I assumed and is why the assertion is written this way.
    """
    nearly_clean = Condition("nearly-clean", legibility=0.999, true_decline=0.999)
    result = power_at(nearly_clean, 20)
    assert result.naive_bias < 1e-5
    assert abs(result.conditioned_width - result.naive_width) < 1e-9


def test_required_prompts_scale_with_illegibility():
    """The planning number: less legible conditions need more data."""
    by_name = {c.name: c for c in CONDITIONS}
    easy = required_prompts_for_width(by_name["text-primary"], 0.05)
    hard = required_prompts_for_width(by_name["image-low-resource"], 0.05)
    assert easy is not None and hard is not None
    assert hard > easy * 2


def test_required_prompts_grow_as_the_target_tightens():
    condition = CONDITIONS[0]
    loose = required_prompts_for_width(condition, 0.10)
    tight = required_prompts_for_width(condition, 0.03)
    assert loose is not None and tight is not None
    assert tight > loose


def test_crossover_is_found_for_every_condition():
    for condition in CONDITIONS:
        assert crossover_sample_size(condition) is not None


def test_detectable_gap_narrows_with_sample_size():
    condition = CONDITIONS[0]
    gaps = [detectable_gap(condition, n) for n in (100, 400, 1600)]
    for earlier, later in zip(gaps, gaps[1:], strict=False):
        assert later < earlier


def test_detectable_gap_is_wider_in_illegible_conditions():
    by_name = {c.name: c for c in CONDITIONS}
    assert detectable_gap(by_name["image-low-resource"], 400) > detectable_gap(
        by_name["text-primary"], 400
    )


@pytest.mark.parametrize("bad", [(-1, 10), (11, 10), (5, 0)])
def test_invalid_wilson_arguments_are_rejected(bad):
    successes, n = bad
    with pytest.raises(ValueError):
        wilson_interval(successes, n)


def test_invalid_planning_arguments_are_rejected():
    with pytest.raises(ValueError):
        power_at(CONDITIONS[0], 0)
    with pytest.raises(ValueError):
        required_prompts_for_width(CONDITIONS[0], 0.0)
    with pytest.raises(ValueError):
        required_prompts_for_width(CONDITIONS[0], 1.5)
