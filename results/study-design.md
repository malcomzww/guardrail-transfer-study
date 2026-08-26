# Study design: what the control costs

The comprehension control is unbiased. That is not sufficient. It works by **discarding observations** -- only inputs the model demonstrably parsed are counted -- so it buys accuracy with precision, and it depends entirely on a probe that is itself an instrument.

Both objections are answered here with numbers, because both are the first things a reviewer should raise.

## Cost in precision, at 400 prompts

| condition | legibility | usable | naive bias | naive error | conditioned error | worth it |
|---|---|---|---|---|---|---|
| `text-primary` | 0.99 | 396 | 0.0020 | 0.0409 | **0.0393** | yes |
| `text-secondary` | 0.84 | 336 | 0.0320 | 0.0686 | **0.0426** | yes |
| `text-low-resource` | 0.61 | 244 | 0.0780 | 0.1102 | **0.0501** | yes |
| `image-primary` | 0.72 | 288 | 0.0560 | 0.0905 | **0.0462** | yes |
| `image-low-resource` | 0.38 | 152 | 0.1240 | 0.1500 | **0.0629** | yes |

*Error* is bias plus half the interval width -- how far the estimate can sit from the truth. Not a rigorous combined interval, but it is the right comparison for the decision being made: which estimator lands closer.

On `image-low-resource`, 400 prompts yield **152 usable observations**. The conditioned interval is wider than the naive one as a result -- and still worth it, because the naive estimator's 0.124 of bias exceeds the precision given up.

## Prompts needed for a 5% interval

| condition | legibility | prompts |
|---|---|---|
| `text-primary` | 0.99 | **1,000** |
| `text-secondary` | 0.84 | **1,180** |
| `text-low-resource` | 0.61 | **1,620** |
| `image-primary` | 0.72 | **1,380** |
| `image-low-resource` | 0.38 | **2,600** |

The least legible condition needs **2.6x the prompts** of the most legible one for the same precision, because only the parsed subset counts. A study that budgets uniformly across conditions will be underpowered in exactly the conditions it most wants to measure.

## The probe is an instrument too

Residual bias on `image-low-resource` (legibility 0.38) under probes of varying quality:

| probe | false pass | false fail | estimate | residual bias | admitted |
|---|---|---|---|---|---|
| `ideal` | 0.00 | 0.00 | 0.8000 | **+0.0000** | 0.380 |
| `slightly-easy` | 0.15 | 0.02 | 0.8400 | **+0.0400** | 0.465 |
| `too-easy` | 0.45 | 0.02 | 0.8857 | **+0.0857** | 0.651 |
| `too-hard` | 0.02 | 0.25 | 0.8083 | **+0.0083** | 0.297 |
| `correlated-hard` | 0.02 | 0.25 | 0.8104 | **+0.0104** | 0.238 |

True rate: 0.800.

**A probe that is too easy undoes the control.** At a 0.45 false-pass rate the residual bias is +0.0857 -- unparsed inputs are admitted to the conditioned set, and they decline at 1.0 by definition. That is the same bias the control exists to remove, arriving through the correction itself.

**A probe that is too hard is wasteful rather than wrong** (+0.0083 residual, 0.297 of inputs admitted) -- unless its difficulty correlates with the conditions that lower legibility, in which case it is both (+0.0104). Non-random discarding is biased discarding.

## How good the probe has to be (1% tolerance)

| condition | legibility | max false-pass rate |
|---|---|---|
| `text-primary` | 0.99 | **0.995** |
| `text-secondary` | 0.84 | **0.275** |
| `text-low-resource` | 0.61 | **0.080** |
| `image-primary` | 0.72 | **0.135** |
| `image-low-resource` | 0.38 | **0.030** |

The requirement is roughly **33x stricter** on `image-low-resource` than on `text-primary`. Fewer parsed inputs means more unparsed ones available to leak through, so the probe must be best exactly where the study most depends on it -- and exactly where a probe is hardest to build.

## What this means for the design

- **Budget prompts per condition, not per study.** Uniform allocation under-powers the illegible conditions that carry the finding.
- **Validate the probe before trusting the control**, and validate it in the hardest condition rather than the easiest. A probe with a 3% false-pass rate in clean text may have a much worse one on a rendered page, and that is the number that matters.
- **Report the admitted fraction alongside every conditioned rate.** A rate computed from 24% of the sample is a different kind of claim from one computed from 99%, and hiding that difference is how a well-intentioned correction becomes a worse estimator than the one it replaced.

## Reproduce

```
uv run python scripts/generate_design.py
```

Raw values in [`study-design-raw.json`](study-design-raw.json), committed so the tables can be checked without rerunning.
