"""Generate results/study-design.md and results/study-design-raw.json.

The second and third analysis dimensions: what the comprehension control costs
in sample size, and how good the probe has to be before the control works at all.

    uv run python scripts/generate_design.py

An unbiased estimator is worth nothing if a realistic study cannot afford it, and
worth less than nothing if its probe quietly re-introduces the bias it removes.
Both are answered with numbers here rather than asserted.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from guardrail_transfer_study import (  # noqa: E402
    CONDITIONS,
    PROBES,
    estimate_with_probe,
    max_tolerable_false_pass,
    power_at,
    required_prompts_for_width,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "study-design.md"
RAW = ROOT / "results" / "study-design-raw.json"
BUDGET = 400
TARGET_WIDTH = 0.05
TOLERANCE = 0.01


def main() -> int:
    power = {c.name: power_at(c, BUDGET) for c in CONDITIONS}
    needed = {
        c.name: required_prompts_for_width(c, TARGET_WIDTH) for c in CONDITIONS
    }
    probe_bias = {
        c.name: {p.name: estimate_with_probe(c, p) for p in PROBES}
        for c in CONDITIONS
    }
    budgets = {c.name: max_tolerable_false_pass(c, TOLERANCE) for c in CONDITIONS}

    worst = min(CONDITIONS, key=lambda c: c.legibility)
    best = max(CONDITIONS, key=lambda c: c.legibility)

    # --- assertions on the claims the README makes -----------------------
    # Conditioning must cost precision -- it uses fewer observations. If it did
    # not, the trade this section is about would not exist.
    for c in CONDITIONS:
        if c.legibility >= 1.0:
            continue
        assert power[c.name].conditioned_width > power[c.name].naive_width

    # And it must still be worth paying at a realistic budget.
    for c in CONDITIONS:
        if c.legibility >= 0.95:
            continue
        assert power[c.name].conditioning_pays

    # Sample-size requirement must scale with illegibility.
    assert needed[worst.name] is not None and needed[best.name] is not None
    assert needed[worst.name] > 2 * needed[best.name]

    # An easy probe must re-introduce the bias, or the probe section has no
    # finding.
    assert probe_bias[worst.name]["too-easy"].residual_bias > 0.05

    # And the probe requirement must tighten as legibility falls.
    assert budgets[worst.name] < budgets[best.name] / 5

    lines: list[str] = []
    lines.append("# Study design: what the control costs\n")
    lines.append(
        "The comprehension control is unbiased. That is not sufficient. It works "
        "by **discarding observations** -- only inputs the model demonstrably "
        "parsed are counted -- so it buys accuracy with precision, and it "
        "depends entirely on a probe that is itself an instrument.\n"
    )
    lines.append(
        "Both objections are answered here with numbers, because both are the "
        "first things a reviewer should raise.\n"
    )

    lines.append(f"## Cost in precision, at {BUDGET} prompts\n")
    lines.append(
        "| condition | legibility | usable | naive bias | naive error | "
        "conditioned error | worth it |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for c in CONDITIONS:
        r = power[c.name]
        lines.append(
            f"| `{c.name}` | {c.legibility:.2f} | {r.usable} | "
            f"{r.naive_bias:.4f} | {r.naive_total_error:.4f} | "
            f"**{r.conditioned_total_error:.4f}** | "
            f"{'yes' if r.conditioning_pays else 'no'} |"
        )
    lines.append("")
    lines.append(
        "*Error* is bias plus half the interval width -- how far the estimate "
        "can sit from the truth. Not a rigorous combined interval, but it is the "
        "right comparison for the decision being made: which estimator lands "
        "closer.\n"
    )
    w = power[worst.name]
    lines.append(
        f"On `{worst.name}`, {BUDGET} prompts yield **{w.usable} usable "
        f"observations**. The conditioned interval is wider than the naive one "
        f"as a result -- and still worth it, because the naive estimator's "
        f"{w.naive_bias:.3f} of bias exceeds the precision given up.\n"
    )

    lines.append(f"## Prompts needed for a {TARGET_WIDTH:.0%} interval\n")
    lines.append("| condition | legibility | prompts |")
    lines.append("|---|---|---|")
    for c in CONDITIONS:
        lines.append(
            f"| `{c.name}` | {c.legibility:.2f} | **{needed[c.name]:,}** |"
        )
    lines.append("")
    ratio = needed[worst.name] / needed[best.name]
    lines.append(
        f"The least legible condition needs **{ratio:.1f}x the prompts** of the "
        "most legible one for the same precision, because only the parsed "
        "subset counts. A study that budgets uniformly across conditions will be "
        "underpowered in exactly the conditions it most wants to measure.\n"
    )

    lines.append("## The probe is an instrument too\n")
    lines.append(
        f"Residual bias on `{worst.name}` (legibility {worst.legibility:.2f}) "
        "under probes of varying quality:\n"
    )
    lines.append("| probe | false pass | false fail | estimate | residual bias | admitted |")
    lines.append("|---|---|---|---|---|---|")
    for p in PROBES:
        r = probe_bias[worst.name][p.name]
        lines.append(
            f"| `{p.name}` | {p.false_pass:.2f} | {p.false_fail:.2f} | "
            f"{r.estimated_decline:.4f} | **{r.residual_bias:+.4f}** | "
            f"{r.admitted_fraction:.3f} |"
        )
    lines.append(f"\nTrue rate: {worst.true_decline:.3f}.\n")

    easy = probe_bias[worst.name]["too-easy"]
    hard = probe_bias[worst.name]["too-hard"]
    corr = probe_bias[worst.name]["correlated-hard"]
    lines.append(
        f"**A probe that is too easy undoes the control.** At a 0.45 false-pass "
        f"rate the residual bias is {easy.residual_bias:+.4f} -- unparsed inputs "
        "are admitted to the conditioned set, and they decline at 1.0 by "
        "definition. That is the same bias the control exists to remove, "
        "arriving through the correction itself.\n"
    )
    lines.append(
        f"**A probe that is too hard is wasteful rather than wrong** "
        f"({hard.residual_bias:+.4f} residual, {hard.admitted_fraction:.3f} of "
        "inputs admitted) -- unless its difficulty correlates with the "
        f"conditions that lower legibility, in which case it is both "
        f"({corr.residual_bias:+.4f}). Non-random discarding is biased "
        "discarding.\n"
    )

    lines.append(f"## How good the probe has to be ({TOLERANCE:.0%} tolerance)\n")
    lines.append("| condition | legibility | max false-pass rate |")
    lines.append("|---|---|---|")
    for c in CONDITIONS:
        lines.append(
            f"| `{c.name}` | {c.legibility:.2f} | **{budgets[c.name]:.3f}** |"
        )
    lines.append("")
    lines.append(
        f"The requirement is roughly **{budgets[best.name] / budgets[worst.name]:.0f}x "
        f"stricter** on `{worst.name}` than on `{best.name}`. Fewer parsed "
        "inputs means more unparsed ones available to leak through, so the probe "
        "must be best exactly where the study most depends on it -- and exactly "
        "where a probe is hardest to build.\n"
    )

    lines.append("## What this means for the design\n")
    lines.append(
        "- **Budget prompts per condition, not per study.** Uniform allocation "
        "under-powers the illegible conditions that carry the finding.\n"
        "- **Validate the probe before trusting the control**, and validate it "
        "in the hardest condition rather than the easiest. A probe with a 3% "
        "false-pass rate in clean text may have a much worse one on a rendered "
        "page, and that is the number that matters.\n"
        "- **Report the admitted fraction alongside every conditioned rate.** A "
        "rate computed from 24% of the sample is a different kind of claim from "
        "one computed from 99%, and hiding that difference is how a "
        "well-intentioned correction becomes a worse estimator than the one it "
        "replaced.\n"
    )

    lines.append("## Reproduce\n")
    lines.append("```\nuv run python scripts/generate_design.py\n```\n")
    lines.append(
        "Raw values in [`study-design-raw.json`](study-design-raw.json), "
        "committed so the tables can be checked without rerunning.\n"
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")

    RAW.write_text(
        json.dumps(
            {
                "budget_prompts": BUDGET,
                "target_width": TARGET_WIDTH,
                "tolerance": TOLERANCE,
                "power": {
                    name: {
                        "usable": r.usable,
                        "naive_bias": r.naive_bias,
                        "naive_error": r.naive_total_error,
                        "conditioned_error": r.conditioned_total_error,
                        "conditioning_pays": r.conditioning_pays,
                    }
                    for name, r in power.items()
                },
                "prompts_for_target_width": needed,
                "max_false_pass": budgets,
                "probe_residual_bias": {
                    cname: {
                        pname: r.residual_bias
                        for pname, r in byprobe.items()
                        if r.estimated_decline == r.estimated_decline
                    }
                    for cname, byprobe in probe_bias.items()
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"wrote {OUT.name} and {RAW.name}")
    print(
        f"  {worst.name}: {w.usable}/{BUDGET} usable, "
        f"needs {needed[worst.name]:,} prompts for {TARGET_WIDTH:.0%}"
    )
    print(f"  probe false-pass budget: {budgets[worst.name]:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
