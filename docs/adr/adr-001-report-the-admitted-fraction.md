# ADR 001: report the admitted fraction with every conditioned rate

## Status

Accepted.

## Context

The comprehension control removes a real bias. It does so by discarding
observations — only inputs the model demonstrably parsed are counted — and that
creates two failure modes the corrected number does not display.

**Precision.** On the least legible condition, 400 prompts yield **152 usable
observations**. Reaching a 5% interval there needs **2,600 prompts** against
1,000 for the most legible condition — 2.6x, because only the parsed subset
counts. A study that budgets uniformly across conditions is underpowered in
exactly the conditions carrying its finding.

**Probe validity.** A probe with a 0.45 false-pass rate leaves **+0.0857** of
residual bias on that same condition. That is the bias the control exists to
remove, arriving back through the correction itself. The false-pass budget for
1% residual bias is **0.030** on the least legible condition against **0.995**
on the most — a 33x difference, strictest exactly where a probe is hardest to
build.

A conditioned rate reported as a bare number carries neither fact. Two studies
can report the same rate with one computed from 99% of its sample and the other
from 24%, and nothing distinguishes them.

## Decision

Every conditioned rate is reported with its **admitted fraction** and its
interval. The triple, never the point estimate alone:

```
image-low-resource: 0.800 [0.738, 0.851], n=152/400 admitted (38%)
```

Three further rules follow:

- **Budget prompts per condition, not per study.** Allocation is proportional to
  1/legibility so precision is comparable across conditions.
- **Validate the probe in the hardest condition, not the easiest.** A 3%
  false-pass rate on clean text says nothing about the rate on a rendered page,
  and the rendered page is where the budget is tight.
- **Publish the probe's own error rates** alongside the results. A control whose
  instrument is unvalidated is an assumption wearing a method's clothes.

## Consequences

- Result tables get wider and are harder to skim. That is the intended trade: a
  reader who wants the point estimate can find it, and a reader checking whether
  it is trustworthy now can.
- Some conditions will be honestly reported as underpowered rather than
  reported with a confident-looking rate. That is the correct outcome and the
  one a bare number makes easy to avoid.
- The probe becomes a component with its own validation requirement and its own
  section in the write-up, rather than an implementation detail.

## What would change this

A probe demonstrably at a near-zero false-pass rate across every condition would
make the second rule redundant — but demonstrating that is itself the work, and
the demonstration is what the admitted fraction lets a reader check.

If comprehension can be measured as a graded quantity rather than a binary pass,
the discarding could be replaced by weighting, which would recover most of the
lost precision. That is a better design and it is not this one.
