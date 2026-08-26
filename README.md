# guardrail-transfer-study

**A safety evaluation reports up to 12.2 points of apparent cross-condition
difference on a model whose alignment does not vary at all.** Every point of it
is a reading-ability artifact.

This repo answers one question:

> How much of an apparent cross-modal safety gap is a reading-ability artifact
> rather than an alignment gap?

> **No attack material.** Built and demonstrated on synthetic, harmless
> prompts. There is no attack corpus here, no published safety benchmark and no
> jailbreak text — what is under test is the *estimator*, not any model's
> safety. The dissertation work uses published-benchmark prompts under a release
> policy requiring supervisor sign-off and aggregate-only reporting, and none of
> that is in this repository. A test enforces it.

## The confound

A cross-modal safety evaluation reports a refusal rate per condition and reads
it as alignment strength. But two very different models produce an identical
observation:

- a model that **understood** the request and declined it
- a model that **could not parse** the input at all

Both score as a refusal. Both score as a safety pass. So a model that simply
cannot read a language looks exactly as aligned as one that read the request and
refused.

The fix is a paired **comprehension probe**: a benign task in the same condition
that only a model which parsed the input can pass. Conditioning refusals on
demonstrated comprehension splits the observed gap into an alignment component
and a perception artifact.

## Case 1: the metric invents a gap

Every condition below has the **same** true decline rate by construction. Only
legibility varies.

| condition | comprehension | naive decline | conditioned | apparent gap | real gap | artifact |
|---|---|---|---|---|---|---|
| `text-primary` | 0.99 | 0.802 | 0.800 | — | — | — |
| `text-secondary` | 0.84 | 0.832 | 0.800 | +3.0 pp | +0.0 pp | **100%** |
| `text-low-resource` | 0.61 | 0.878 | 0.800 | +7.6 pp | +0.0 pp | **100%** |
| `image-primary` | 0.72 | 0.856 | 0.800 | +5.4 pp | +0.0 pp | **100%** |
| `image-low-resource` | 0.38 | 0.924 | 0.800 | +12.2 pp | +0.0 pp | **100%** |

The size of the invented gap tracks legibility exactly. `image-low-resource` has
the lowest comprehension rate and the largest fabricated gap — which is the same
ordering a real study would report and read as alignment failure.

## Case 2: the metric hides a real gap

An instrument that explains every gap away measures nothing. Here alignment
genuinely varies, and the naive metric **understates** it:

| condition | comprehension | naive decline | conditioned | apparent gap | real gap |
|---|---|---|---|---|---|
| `text-primary` | 0.99 | 0.861 | 0.860 | — | — |
| `text-secondary` | 0.84 | 0.756 | 0.710 | −10.5 pp | **−15.0 pp** |
| `image-primary` | 0.72 | 0.698 | 0.580 | −16.4 pp | **−28.0 pp** |

**The naive metric understates the real gap by 11.6 points** on
`image-primary`. Non-comprehension inflates the weaker condition's refusal rate
toward the baseline, so the same confound that invents gaps in case 1 conceals
them here.

**The bias has no consistent direction**, which is why it cannot be corrected
with a fudge factor — only with a measurement.

## Case 3: what the correction costs

The estimator being unbiased is not sufficient. It works by **discarding
observations** — only inputs the model demonstrably parsed are counted — so it
buys accuracy with precision. At a 400-prompt budget:

| condition | legibility | usable | naive error | conditioned error | worth it |
|---|---|---|---|---|---|
| `text-primary` | 0.99 | 396 | 0.041 | **0.039** | yes |
| `text-secondary` | 0.84 | 336 | 0.069 | **0.043** | yes |
| `text-low-resource` | 0.61 | 244 | 0.110 | **0.050** | yes |
| `image-primary` | 0.72 | 288 | 0.091 | **0.046** | yes |
| `image-low-resource` | 0.38 | 152 | 0.150 | **0.063** | yes |

*Error* is bias plus half the interval width — how far the estimate can sit from
the truth. The conditioned interval is genuinely **wider** in every condition,
and the correction still pays everywhere, because the bias it removes exceeds
the precision it gives up.

The planning consequence is sharper. For a 5-point interval:

| condition | legibility | prompts needed |
|---|---|---|
| `text-primary` | 0.99 | 1,000 |
| `image-low-resource` | 0.38 | **2,600** |

**The least legible condition needs 2.6x the prompts** for the same precision. A
study that budgets uniformly across conditions is underpowered in exactly the
conditions carrying its finding.

## Case 4: the probe is an instrument too

Every result above assumes the comprehension probe is valid. That assumption is
doing all the work. Residual bias on `image-low-resource` under probes of
varying quality:

| probe | false pass | false fail | residual bias |
|---|---|---|---|
| `ideal` | 0.00 | 0.00 | +0.0000 |
| `slightly-easy` | 0.15 | 0.02 | +0.0400 |
| `too-easy` | 0.45 | 0.02 | **+0.0857** |
| `too-hard` | 0.02 | 0.25 | +0.0083 |
| `correlated-hard` | 0.02 | 0.25 | +0.0104 |

**A probe that is too easy undoes the control.** Unparsed inputs are admitted to
the conditioned set, and they decline at 1.0 by definition — the same bias the
control exists to remove, arriving back through the correction itself.

A probe that is **too hard** is wasteful rather than wrong (+0.0083) — unless its
difficulty correlates with whatever lowers legibility, in which case it is both
(+0.0104). Non-random discarding is biased discarding.

How good does the probe have to be? For residual bias under 1 point:

| condition | legibility | max false-pass rate |
|---|---|---|
| `text-primary` | 0.99 | 0.995 |
| `text-low-resource` | 0.61 | 0.080 |
| `image-low-resource` | 0.38 | **0.030** |

**33x stricter** where legibility is lowest — the probe must be best exactly
where the study most depends on it, and exactly where a probe is hardest to
build.

Full tables: [`results/study-design.md`](results/study-design.md).
[ADR 001](docs/adr/adr-001-report-the-admitted-fraction.md) records what this
means for how results get reported.

## Why this matters

The cross-modal safety literature reports refusal rates falling when a harmful
request arrives as an image, or in a lower-resource language, and reads that as
safety training failing to transfer.

Case 1 shows an evaluation producing exactly that result on a model whose
alignment does not vary at all. Case 2 shows the same confound concealing a real
gap. **Neither the presence nor the absence of an apparent gap licenses a
conclusion about alignment** without a paired comprehension measurement.

Full tables: [`results/comprehension-control.md`](results/comprehension-control.md).

## Limitations

- **This validates an estimator, not a model.** No model is evaluated here and
  no safety claim is made about any system.
- **Closed-form, not sampled.** The bias is an analytic property of the design,
  so sampling would add noise that obscures it. Cases 3 and 4 close part of this
  gap analytically — interval widths, sample-size requirements and probe
  sensitivity — but a real study still needs sampled intervals rather than
  planning arithmetic.
- **Legibility is binary per input.** Real comprehension is graded — a model can
  parse half a request — and a partially understood harmful instruction is a
  case this decomposition does not cover.
- **Probe error rates are stated, not measured.** Case 4 shows how the
  estimator responds to probe quality; it says nothing about how good any real
  probe is. Establishing that is a separate empirical task, and per ADR 001 it
  has to be done in the hardest condition rather than the easiest.

## Reproduce

```bash
uv sync --extra dev
uv run python scripts/generate_results.py
uv run python scripts/generate_design.py
uv run pytest
```

Closed-form arithmetic — identical output on any machine. CI regenerates the
results and fails on any diff.

## License

MIT
