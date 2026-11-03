# Reviewer 1 (Methodology): "Spend Pixels Where It Hurts: Hazard-Aware Rendering for Optical Long-Context Compression"

## 1. Summary
The paper proposes a training-free renderer for black-box VLMs. It flags high-entropy strings with regexes (Detect), enlarges them while shrinking prose under a patch-count budget (Allocate, S), appends verbatim text copies of the flagged strings (Anchor, X), and falls back to plain text when the anchor-to-image cost ratio exceeds τ (Route). Evaluation covers RULER NIAH at 16K–128K characters, a 1–256 needle density sweep, 60 natural-identifier questions built from LongBench, and LongBench QA, across six readers, with N=20–60 per cell and paired item-level bootstrap CIs. The allocation result (S vs A/U/Z/R) is fairly well supported. The anchor results (K, X, and the routed frontier) are much weaker than the paper presents them: in most tasks the anchor list contains the gold answer and few or no distractors, and the scoring does not penalize extra outputs. The "no loss" comprehension claim rests on CIs that are compatible with sizeable losses.

## 2. Criteria committed (written before detailed reading)
1. Budget parity is defined in the unit actually billed, or the mismatch is quantified per provider.
2. Scoring cannot be gamed by over-generation: precision or exact-set metrics sit alongside recall.
3. Information leakage in auxiliary channels (here, anchors) is controlled, e.g., with distractor anchors.
4. Effect sizes come with CIs at the level claimed (pooled means, not only per-cell ones), and there is a multiplicity policy for vote counts.
5. Null claims ("no loss") use pre-specified non-inferiority margins.
6. Thresholds and design choices are fit on data disjoint from the reported evaluation.
7. Natural data are sampled independently of the method's own detector.
8. Reader sets are consistent across experiments, or differences are explicit and analysed.
9. Run-to-run variance and API reproducibility are reported.

## 3. Strengths
- The random-enlargement control R matches total occurrence length (ruler_niah.py) and isolates targeting from enlargement: S−R is significant in 14/15 cells at each budget.
- Counts are reproducible from the logs. From analysis_ruler.json I recomputed S>A in 33/36 cells, S>U in 31/36, S>Z in 32/36, and 0 cells where S is significantly worse.
- Costs are the providers' billed tokens, not the formula, and provider exceptions are disclosed (Limitations).
- The paper is candid about development history: the discarded NIQ v1, the detector revised after a LongBench F1 loss and then re-tested on a fresh sample, and the frontier being in-sample (App. A).
- The detector oracle ablation (Tab. detector) cleanly shows a fallback to uniform rendering when hazards go undetected.

## 4. Weaknesses

**CRITICAL 1: Anchors reveal the answer, and the scoring rewards dumping them (Sec. 5.1, 5.3, 5.4; analyze_ruler.py `score`).**
I checked manifest.json for each run:
- single_3: 1.0 anchors per item on average, and the gold value is in the list 25/25 times. The anchor *is* the answer.
- multivalue: about 4.3 anchors per item, which are essentially the four gold values.
- multikey: 4–11 anchors, of which 4 are needles.
- density k=16: about 16 anchors.
- NIQ: gold is in the anchors 60/60 times, by construction, with a mean of 6.4 anchors and some items having exactly 1.

Scoring is case-insensitive containment over a returned list, with no precision penalty. The readers do exploit this. In rdens_k16, Qwen returns 16.0 ids per item under X (up from 2.6 under A), and in all 25 items it returns more ids than gold values; GPT returns 11.8 per item. In rbx_s6_multikey_1, Qwen and MiniMax over-answer in 25/25 X items.
- Why it matters: K≈0.97 and X≈0.98–1.00 on RULER, "X beats K by 0.10 at k=16", the routed frontier, and NIQ's 0.76 may largely reflect copying the anchor list, not reading the image. The paper's own claim that anchors "do not say which key a string belongs to, so the reader must still locate it" does not hold under this metric.
- Fix:
  - Rescore with exact-set or precision-aware metrics (F1 over returned values; or require exactly as many values as gold).
  - Report the mean number of returned values per arm.
  - Add a decoy-anchor control: anchors with non-answer flagged strings, or shuffled anchors from other items at the same count.
  - On NIQ, report a baseline that picks a random anchor.

**MAJOR 1: The NIQ target sampling is circular (Sec. 5.4, App. niq; niq.py `candidates`).**
Targets must be flagged by the same detector, so the set measures performance conditional on detection. It says nothing about natural identifiers the detector misses, and that miss rate is the risk the paper flags (missed hazards get shrunk with prose).
- Fix: sample targets with a detector-independent rule (e.g., any token with a digit, or human-annotated verbatim spans), then report detector recall and S/X recall on detected and undetected targets.

**MAJOR 2: "No significant loss" is treated as "no loss" (Tab. longbench, abstract).**
With N=50, per-cell S−A lower bounds reach −0.10 to −0.12 F1 (lb2/lb3: MiniMax mfqa −0.124, Qwen hotpot −0.124), on bases of 0.23–0.66. The two reads of the same documents disagree on which cells are significant, which shows that run-to-run variance at temperature 0 is non-trivial.
- Fix:
  - Pre-specify a non-inferiority margin (e.g., −0.03 F1) and test pooled S−A and X−A with a reader-by-item hierarchical bootstrap.
  - Report repeat-run variance.
  - Add plain text (T) to the table. The logs show A itself trails T by up to 0.32 F1 (lb_s6, Llama), which matters for the deployment claim.

**MAJOR 3: Headline means have no CIs and there is no multiplicity policy (abstract; Sec. 5.1–5.2).**
"+0.45–0.49", "63 of 72", and "46 of 54 cells" are counts of uncorrected per-cell percentile-bootstrap tests at n=20–25 with binary outcomes. Several cells sit exactly at a lower bound of 0.000, a discretization artifact.
- Fix: fit a mixed-effects logistic model (arm fixed effect; reader and item random effects) or use a two-level bootstrap. Report pooled effects with CIs, and apply Holm/BH to the cell counts.

**MAJOR 4: The reader sets shift between experiments (Tab. baselines †, Tab. detector, Tab. niq, Fig. density c).**
The R and X arms omit Claude; the detector ablation and NIQ use 5 readers; costs use 4–5 readers; the routing frontier uses 4; the held-out Claude reader is an agent with estimated costs and N=10. Means such as "X 1.00 vs K 0.95" mix subsets; the caption fixes this for K, but the text does not do so consistently.
- Fix: report every headline on the common reader subset, with per-subset tables in the appendix.

**MAJOR 5: The budget parity is only nominal (Eq. 1; Sec. 4).**
- Gemini bills *more* for S than for A at 16K/32K (1176 vs 1151; 1184 vs 1161), and Llama bills identically.
- S runs well under the formula budget (540 vs 756 vtok at 16K/6px), so the "equal budget" is really "at most".
- U is chosen to maximize size, not tuned for recall.
- Provider-side resizing is not characterized, so glyph sizes on the model side are unknown.
- Fix: report per-provider billed parity, and give U/Z the same budget slack or a small recall-tuned search on a dev split.

**MAJOR 6: The router threshold is not cleanly held out (Sec. 3.5, App. A).**
τ is cross-validated on the density sweep. Its median (0.3) is then applied in-sample to the same sweep for the per-density numbers and the 0.97@0.69× claim. The "held-out" corpora profile has no accuracy labels, and the held-out Claude reader has N=10 per cell. The router also uses a fixed objective weight of 0.5 in recall − 0.5·cost.
- Fix: select τ on a separate density sweep (new seed) and evaluate on NIQ or LongBench, with sensitivity analysis over the weight.

**MINOR**
- The "silent near-miss" metric (same length, SequenceMatcher ≥ 0.6) is arbitrary; report a sensitivity analysis over the threshold.
- 238 outputs are scored zero as unparseable, and they concentrate in K/X at high k (Qwen k=64: 24/25 of X items). Report this per arm, since it confounds the K vs X comparison at high density.
- LongBench is evaluated only at 6 px; comprehension at 5 px, where line spacing is removed, is untested.
- Reproducibility: there is a single run per configuration over three days with no model snapshot IDs. Report a repeat run on one task.
- The NIQ v1 rejection and the GLUED filter were designed after outcomes were seen. Disclose how the regex was chosen and report v1 results in the appendix.

## 5. Questions for the authors
1. What are K/X recall and precision when scoring requires exactly the gold number of values?
2. What is the NIQ recall of a baseline that outputs one random anchor?
3. What is the detector's recall on detector-independent natural identifiers?
4. What are the pooled S−A, X−A, and X−K effects with hierarchical CIs?
5. How do providers resize 1008×2016 pages, and what are the effective glyph sizes on the model side?

## 6. Criterion judgements
- **Novelty:** PARTLY_MEETS. Content-aware allocation at render time is new; anchors amount to an append-the-strings baseline.
- **Technical soundness:** PARTLY_MEETS. The allocation logic is sound; the anchor evaluation is confounded by answer leakage and recall-only scoring.
- **Experimental validation:** DOES_NOT_MEET for the anchor and routing claims; PARTLY_MEETS for allocation (good controls, but small N, no pooled CIs, a circular NIQ set).
- **Clarity:** MEETS. Arms, exceptions, and history are clearly documented.
- **Significance:** PARTLY_MEETS. The gain from allocation alone is large but leaves recall at 0.48–0.66; the practical case depends on anchors, which are not yet validly measured.

## 7. Recommendation: Major revision
Changes that would most move this:
1. Precision-aware or exact-set rescoring of all K/X/routing results, plus decoy-anchor controls.
2. A detector-independent natural-identifier set.
3. Pooled hierarchical CIs with a non-inferiority test for LongBench and multiplicity control for the cell counts.
