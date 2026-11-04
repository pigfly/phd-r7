# Reviewer 1 (Methodology), Re-review (Stage 3')

I audited the revised PDF, `git diff HEAD~1 -- paper/sec`, `rescore.py`, `stats_pooled.py`, `niq.py --anytarget`, `make_items.py:render_box`, and the analysis JSONs. The following numbers match the evidence: every row of Tab. 2 (`analysis_pooled.json`, `ci_readers_items`, Holm counts), Tab. 3 (niq2_s6/niq3_s6), Tab. 4 (lb3, including T), the NIQ frontier (1017/1128/1306 and 1014/1267/1345), the 31%/29% savings at 64K/128K, and the 12% saving on NIQ. I found no case of gaming by concatenation: 0 of 6,544 returned strings contain two or more anchors.

## 1. Revision checklist

| Item | Status | Evidence |
|---|---|---|
| CRIT 1: anchor leakage, recall-only scoring | PARTIALLY_RESOLVED | Precision-aware F1, number of values returned, gold-in-anchors rate, and a random-pick baseline were added (rescore.py). §5.5 now says that on RULER the anchor list *is* the answer. The decoy/shuffled-anchor control was not run; niq3 (gold in anchors 1/60) serves as a natural decoy. The long-context K/X claim is still recall-only (N1). |
| MAJOR 1: circular NIQ sampling | RESOLVED | niq3: any digit-bearing token, new seed; detector recall reported (1/60). Residual: the six-word prefix must still be unflagged (`niq.py` l.27). |
| MAJOR 2: "no significant loss" read as "no loss" | PARTIALLY_RESOLVED | T was added; X−T is significantly negative in 9/10 cells, and this is stated in the abstract. Still missing: a non-inferiority margin, a pooled LongBench S−A/X−A row in Tab. 2, and repeat-run variance. Per-cell lower bounds still reach −0.12 (Qwen hotpot S−A [−0.124, −0.006]), yet the abstract says QA is "without changing" and Tab. 4 says "cost no comprehension". |
| MAJOR 3: pooled CIs, multiplicity | RESOLVED (with N2) | Cluster bootstrap plus Holm within each comparison; Tab. 2. |
| MAJOR 4: reader sets | RESOLVED (residual N6) | One fixed set of 5 readers for all means and tests. |
| MAJOR 5: nominal budget parity | UNRESOLVED (now MINOR) | No slack or recall-tuning for U/Z, and no characterization of provider resizing. Its importance is reduced because the 8/10 px results show U catching up. |
| MAJOR 6: router τ in-sample | PARTIALLY_RESOLVED | Routing was moved to the appendix and labelled in-sample. Acceptable given the narrowed claims. |
| MINOR: near-miss threshold | RESOLVED (moot) | The metric was removed from the paper. |
| MINOR: unparseable outputs per arm | UNRESOLVED | Only a global 0.25% drop rate is given, not wrong-by-unparseable counts per arm. |
| MINOR: LongBench at 5 px | UNRESOLVED | — |
| MINOR: repeat run, snapshot IDs | UNRESOLVED | Readers are still identified only by model name. |
| MINOR: NIQ v1 disclosure | PARTIALLY_RESOLVED | It is described (14/60 artifacts) and the logs are released, but the v1 numbers are not reported. |

## 2. New issues

**MAJOR N1: The long-context K-vs-X claim uses the metric the paper itself rejects (Intro contribution 3; §5.5 "at 64K and 128K … 31% and 29% fewer").**
On rv2_c{64,128}k_multikey_1 the anchors contain the gold value 100% of the time and readers return 4.2–5.1 values for 4.9–6.0 anchors.
- Under F1: K = 0.38/0.39 and X = 0.40/0.36; exact-set accuracy is 0.03–0.09; pooled X−K F1 = −0.005 [−0.05, 0.04].
- S alone, with no anchors, has the same F1 (0.39/0.38) as X at the same cost.
- At 8/10 px, anchors *lower* multi-key F1 relative to the image alone (S 0.57/0.61 vs X 0.48/0.49).
- The "equal recall at 30% fewer tokens" result is therefore the copying measurement that §5.5 says should not be interpreted.
- Fix: report F1 for this comparison, or drop it. Restate it as "allocation lowers the cost of anchors", not "anchors on S match K's accuracy".

**MINOR N2: The cluster bootstrap resamples readers independently within each run (`stats_pooled.py`, `draw`: `rds=[R.choice(rds) …]` inside the run loop).**
Readers are crossed with runs, so one reader draw per replicate should be shared across runs. I recomputed it that way:
- tab1_s6 S−A becomes [0.27, 0.57] (reported [0.31, 0.55]).
- B−A becomes [−0.136, −0.001].
- X−K F1 at 6 px becomes [+0.001, +0.082].

The conclusions hold, but the borderline rows now touch zero. With only 5 reader clusters the bootstrap is also anticonservative. Separately, the cell p-values come from 1,000 resamples, so Holm over 45 cells (threshold 0.0011) effectively requires zero reversals.
- Fix: share the reader draw across runs, and add a mixed-effects logistic model as a check.
- Fix: use an exact sign-flip or McNemar test per cell.

**MINOR N3: Tab. 2 reports X−K only where it is positive.** Omitted:
- 16K at 5 px: +0.003 [−0.02, 0.03]
- density F1: −0.014
- 64K–128K F1: −0.005
- 8/10 px F1: −0.001

Add these rows.

**MINOR N4: The wording on the niq3 nulls goes beyond the data.**
- "Allocation neither helps nor hurts": S−A = −0.01 with CI [−0.11, +0.08], which is inconclusive.
- "Anchors mislead readers": X−A CI [−0.19, 0.00] and X−K CI [−0.17, +0.01] include zero. K−A = −0.01, so the drop is specific to X, and X−S was never tested.
- Fix: soften the claims in §5.5 and the Limitations.

**MINOR N5: The NIQ anchor count is ambiguous.** "6.4 anchors" counts duplicates; there are 5.27 unique anchors, which is what the pick baseline of 0.44 uses. 14/60 items have a single unique anchor, which is the answer. Report both counts, and K/X on items with at least 2 unique anchors.

**MINOR N6: Reader-set residue.** Fig. 5 recall averages six readers, the Tab. 5 "Mean" row includes Claude (0.20 vs 0.12 for the five-reader mean in the text), and Fig. 5c uses four readers.

**MINOR N7: The box control is not purely about salience.** `render_box` draws a 1-px rectangle flush against 6-px glyphs with 1 px of leading, which can clutter adjacent characters. B−A = −0.05 should not be read as "salience hurts". Use padding or an underline, or say so.

**MINOR N8: Small range errors.** The frontier gap is 0.02–0.05, not 0.02–0.04 (7 px: 0.813 vs 0.767). The lower end of X−T is 0.145.

## 3. Criteria

1. Budget in billed units: PARTLY_MEETS.
2. Precision-aware scoring: PARTLY_MEETS (added, but N1 sidesteps it).
3. Leakage control: PARTLY_MEETS (natural decoy only).
4. Pooled CIs with multiplicity control: MEETS (with the N2 fix).
5. Non-inferiority for null claims: DOES_NOT_MEET.
6. Held-out thresholds: PARTLY_MEETS (demoted).
7. Detector-independent natural data: MEETS.
8. Consistent readers: MEETS.
9. Run-to-run variance: DOES_NOT_MEET.

Overall:
- Novelty: PARTLY_MEETS (narrowed to Allocate; AGAR is close).
- Soundness: MEETS for allocation.
- Experimental validation: PARTLY_MEETS (allocation is now well supported, with the boxed and random-word controls, the milder-budget boundary, and pooled CIs).
- Clarity: MEETS.
- Significance: PARTLY_MEETS.

## 4. Recommendation: Minor Revision

Required changes:
1. Restate the 64K/128K K-vs-X result with F1, or remove it from the contributions (N1).
2. Add a pooled LongBench S−A/X−A test with a pre-stated non-inferiority margin (e.g., −0.05 F1), and align the abstract and the Tab. 4 caption with it. Soften the niq3 null and "mislead" wording (N4).
3. Fix the bootstrap reader resampling and add the omitted X−K rows (N2, N3).

Recommended: one repeat run on a single task, and unparseable-output counts per arm.
