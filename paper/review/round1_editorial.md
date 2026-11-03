# Stage 3 — Editorial Decision Letter (Round 1)

**Manuscript:** Spend Pixels Where It Hurts: Hazard-Aware Rendering for Optical Long-Context Compression (CVPR 2027, review copy)
**Decision: MAJOR REVISION**
**Panel provenance:** the five seats are Claude subagents (same model family and provider, Anthropic). Each started in a fresh context with read-only access to the manuscript and evidence files, and none could see the others' reports before committing its own. That is role separation within one model family, not independence between reviewers. No accountable human reviewer took part. Calibration status: NOT_CALIBRATED.

| Seat | Recommendation | CRIT / MAJ / MIN |
|---|---|---|
| Journal-Fit (EIC) | Major (borderline Reject) | 1 / 4 / 3 |
| R1 Methodology | Major | 1 / 6 / 5 |
| R2 Domain | Major | 1 / 4 / 4 |
| R3 Perspective | Major | 1 / 6 / 3 |
| Devil's Advocate | core claims survive only partly | 1 / 5 / 4 |

## 1. What the panel agrees holds up
- **S beats A, U and Z at equal budget, and the targeting is what drives it.** All five reports accept this. R (random words, length-matched) stays at about 0.10, while S−R is significant in 14/15 cells. R1 recomputed the counts from the logs.
- **Billed tokens are the cost unit**, and the billing exceptions are disclosed.
- **The disclosures are honest:** the discarded NIQ v1, the detector history, the in-sample frontier, and the negative cells.
- **Missed hazards degrade only to uniform rendering** (oracle ablation).

## 2. Consensus issues (raised by three or more seats)
1. **K is the real baseline, and X adds little over it** (EIC W1, R2 W4, R3 W5, DA C1/M1; R1 is related). K is 0.97/0.95 on RULER and 0.74 on NIQ; X is 0.98/1.00 and 0.76. The X−K advantage is mostly the roughly 10% cost saving. K at 5 px (823 tokens, 0.97) may match X at 6 px (881 tokens). K and X are never run at 32K–128K.
2. **LongBench leaves out plain text** (EIC W5, R1 M2, R3 W1-CRIT, DA M2). The evidence file already contains an A−T gap of about −0.18 F1, significant in 9/12 cells. "No significant loss" is measured against uniform images, not against text.
3. **NIQ targets are selected by our own detector (circular)** (EIC W4, R1 M1, DA M3). Missed natural identifiers are never measured.
4. **The operating point sits at the floor of uniform rendering** (R2 W2, DA M5, EIC W6). 5–6 px Menlo with character wrapping puts four readers at about 0. There is no long-context result at 8–10 px or with a proportional font.
5. **Reader sets differ across experiments, and there is no multiplicity control or pooled CI** (EIC W3, R1 M3/M4, R3 W9, DA m1/m2).
6. **No trained optical compressor and no pruning baseline** (EIC W2, R2 W1-CRIT/W3).
7. **The router is calibrated in-sample on synthetic data** (EIC W7, R1 M6, R3 W8, DA m3).

## 3. Adjudication of each CRITICAL (visible, as required)

| # | Source | Claim | Verdict | Reason |
|---|---|---|---|---|
| C-DA | Devil's Advocate C1 | Detector (windowed entropy at 3.5 bits), anchors and routing come from *Render or Retain* (ref/main.pdf), which the paper does not cite | **VALIDATED: author decision required** | Checked: the R-or-R abstract contains "windowed-entropy detector", "selective exact-anchor sidecar" and density routing, and thoughts/01 records it as the starting point. The paper currently presents these as "generic baselines we build". If a reviewer knows R-or-R, this reads as unattributed reuse, which is a desk-reject or integrity risk. **It conflicts with the user's earlier decision not to cite R-or-R**, so the editor does not overrule it and hands the decision back to the author (see checkpoint). |
| C-R1 | Methodology CRIT 1 | Anchors contain the answer (single_3: one anchor per item, and it is the gold value), and recall-only scoring rewards dumping the anchor list | **VALIDATED** | This does not affect the S/A/U/Z/R conclusions (no anchors there). It does affect the meaning of all K/X/NIQ/routing numbers and the claim that "the reader must still locate it". Needed: exact-set or F1 scoring, mean number of returned values, decoy-anchor controls, and a random-anchor baseline on NIQ. |
| C-R3 | Perspective W1 | The LongBench comparison has no plain-text reference | **VALIDATED** | numbers.json has longbench_lb_text, but it is a different sample. Needed: rerun T on the same LB samples (cheap) and qualify "no loss" in the abstract. |
| C-EIC | Fit W1 | No cost-matched X vs K frontier, so the vision contribution is not established | **VALIDATED** | Overlaps consensus issue 1. Sweep s0 ∈ {4,5,6,(7)} for K and X on one reader set, for both RULER and NIQ. |
| C-R2 | Domain W1 | No trained optical compressor (Glyph / DeepSeek-OCR) used as a reader | **DOWNGRADED TO MAJOR** | The paper explicitly targets black-box general VLMs, and running a trained compressor needs local GPU inference. This is a scope question, not something that overturns a main claim. One open-weight compressor reader, if feasible, or a principled scoping paragraph plus a comparison on the compression–recall axis using FocusVTC's published numbers, is enough. |

**DA-CRITICAL-VS-ACCEPT: 1 validated/unresolved (C-DA).** It blocks Accept and requires the author's decision.

## 4. Points where the reviewers disagree
- **R1 vs. the others on how serious the anchor issue is.** R1 calls it DOES_NOT_MEET for the anchor claims; the others treat K/X as valid but of small marginal value. The editor sides with R1 on the *interpretation*: K/X recall is partly copying from the list. The practical value still stands if precision-aware scoring confirms it.
- **DA M4 (salience vs. legibility).** Only DA raised this. It is plausible, since NIAH rewards finding the needle. The cost is low (bold or boxed at prose size, plus an "enlarge all flagged strings including distractors" control), so it goes on the roadmap.

## 5. Revision Roadmap (immutable core; ordered by effect on the decision)

**P0: decision-blocking**
- **RM-1 (C-DA): attribution of R-or-R.** Author decision (see checkpoint). If cited: narrow the novelty to budget-constrained allocation, call K / routing the "prior-work baseline", and make X vs that baseline the headline.
- **RM-2 (C-R1): anchor leakage.** Rescore K/X/NIQ/routing with exact-set and F1 metrics. Report the number of returned values per arm. Add decoy anchors (shuffled flagged strings from other items at the same count) and a random-anchor NIQ baseline. *No new API calls are needed for rescoring; the decoy runs are small.*
- **RM-3 (C-R3): plain text T on the same LongBench samples.** Add it to Tab. 3, rewrite the abstract and conclusion ("usable" → state the cost–accuracy trade-off against text).
- **RM-4 (C-EIC / consensus 1): matched-cost frontier of K vs X.** s0 ∈ {4,5,6} on one fixed reader set, for RULER and NIQ. Add K/X at 64K/128K. If X does not dominate, reframe X as the cost-optimised form of K.

**P1: major**
- RM-5: a NIQ subset independent of the detector (e.g., any token containing a digit, or LLM-labelled must-copy spans). Report detector recall and A/S/X recall on detected vs undetected targets.
- RM-6: at least one long-context budget with a gentler regime (8–10 px, and/or a proportional font with word wrapping).
- RM-7: statistics. Pooled effects with hierarchical or two-level bootstrap CIs, Holm/BH for the cell counts, a non-inferiority margin for LongBench, one fixed reader set per headline, and model snapshot IDs.
- RM-8: salience control (bold or boxed needle at prose size) and an "enlarge all flagged strings" control.
- RM-9: router τ chosen on a new-seed sweep and evaluated on NIQ; sensitivity to the 0.5 weight.
- RM-10: scope for trained compressors and pruning. Either one open reader (Glyph / DeepSeek-OCR, or Qwen3-VL with VisionZip) or a principled scoping paragraph plus a FocusVTC comparison point.
- RM-11: deployment paragraph in the limitations: prompt caching (anchors placed before the question), latency, non-ASCII, billing sensitivity, and text filters bypassed by images.

**P2: minor**
- RM-12: abstract/contribution ranges made consistent (0.45–0.49 vs 0.42–0.57); "63 of 72" explained.
- RM-13: exact-match (case-sensitive) metric alongside the current one; sensitivity of the near-miss threshold; unparseable outputs reported per arm.
- RM-14: soften "silent" and "same kind of strings" (Sec. 2).
- RM-15: missing references (verify each before adding): DocOwl2, TextMonkey, Donut, PIXAR, PixelWorld, LLMLingua-2, Prompt Cache.
- RM-16: near-miss character-confusion analysis and a crop-and-read localization-vs-transcription probe (optional; this is R2's request for vision insight).

## Attachment: Acronym Check (advisory, #849)
### Acronym check (advisory; no reply needed)
Coverage: body (partial)
Not in this input: English abstract, Chinese abstract.
Not checked:
- Body, line 81: VLM (the initials before its parentheses do not spell it)

| Scope | Line | Rule | Acronym | Uses |
|---|---|---|---|---|
| Body | 1 | Not defined | CVPR | 46 |
| Body | 4 | Not defined | COPY | 15 |
| Body | 4 | Not defined | DO | 15 |
| Body | 4 | Not defined | NOT | 15 |
| Body | 4 | Not defined | REVIEW | 15 |
| Body | 89 | Not defined | RULER | 16 |
| Body | 98 | Not defined | QA | 4 |
| Body | 209 | Not defined | UUID | 5 |
| Body | 226 | Not defined | HAR | 1 |
| Body | 227 | Not defined | TECT | 1 |
| Body | 229 | Not defined | NCHOR | 3 |
| Body | 231 | Not defined | ROUTE | 4 |
| Body | 295 | Not defined | OCR | 5 |
| Body | 307 | Not defined | SEER | 2 |
| Body | 358 | Not defined | FCoT | 2 |
| Body | 358 | Not defined | ToMe | 1 |
| Body | 358 | Not defined | VL | 14 |
| Body | 462 | Not defined | KV | 2 |
| Body | 481 | Not defined | ETECT | 3 |
| Body | 483 | Not defined | CHOR | 1 |
| Body | 518 | Not defined | IP | 1 |
| Body | 689 | Not defined | CPU | 1 |
| Body | 795 | Not defined | A22B | 1 |
| Body | 795 | Not defined | GPT | 11 |
| Body | 795 | Not defined | VL235B | 1 |
| Body | 859 | Not defined | ASCII | 3 |
| Body | 875 | Not defined | JSON | 2 |
| Body | 1857 | Not defined | ViT | 1 |
| Body | 1895 | Not defined | LLM | 8 |
| Body | 1906 | Not defined | LLaVA | 2 |
| Body | 1921 | Not defined | SnapKV | 1 |
| Body | 1928 | Not defined | EMNLP | 1 |
| Body | 2062 | Not defined | VPRune | 1 |
| Body | 2081 | Not defined | CVF | 3 |
| Body | 2081 | Not defined | IEEE | 3 |
| Body | 2089 | Not defined | CLIPPO | 1 |
| Body | 2127 | Not defined | TRIO | 1 |
| Body | 2257 | Not defined | PIL | 1 |
| Body | 2711 | Not defined | BIBREF | 1 |
| Body | 2791 | Not defined | RECORD | 1 |
| Body | 2808 | Not defined | API | 3 |
| Body | 2895 | Not defined | LB | 13 |
