# Reviewer 3 Re-review (Stage 3'): ML systems / serving cost

## 1) Revision response checklist

| Item | Status | Evidence / anchor |
|---|---|---|
| **W1** (CRIT) No plain-text reference on LongBench | **RESOLVED** | Tab. 4 now has a T column and billed tokens (T 0.58/0.73 vs. X 0.33/0.56). §5.6 says that X−T is significantly negative in 9 of 10 cells (0.15–0.33). The abstract says that "all image arms remain well below plain text on ordinary QA", and the limitations repeat this. I checked the numbers against `analysis_longbench.json` (lb3): the 9/10 count is right, and the one non-significant cell is GPT-6 Luna on HotpotQA (−0.02 [−0.14, 0.10]). The cost ratio of "a fifth to a quarter" (1153/5617 and 1355/5342) is also right. |
| **W2** (MAJOR) No practical non-optical baselines | **PARTIALLY_RESOLVED** (declined) | LLMLingua-2 and Prompt Cache are now cited. §2 states that caching is "a competing way to cut cost that we do not evaluate". There is still no text-compression baseline and no cost model over queries per document. The contribution is now narrowed to *allocation*, so image-vs-image is the right primary comparison, and I accept this for a CVPR paper. |
| **W3** (MAJOR) Cacheability claimed but not measured; anchors placed after the question | **PARTIALLY_RESOLVED** | Caching appears in the limitations (§6). However, the intro ("can be cached and reused") and §2 ("cached and reused across queries") still sell it as a benefit. App. A still puts anchors after the question for RULER and NIQ. See N2. |
| **W4** (MAJOR) K/X never run at long context | **PARTIALLY_RESOLVED** | K/X were run at 64K/128K, but only on multi-key, which §5.5 itself says "measures copying rather than reading". See N1. |
| **W5** (MAJOR) Small margin of X over K | **RESOLVED** (framing) | Matched-cost frontier at 5/6/7 px. X−K is +0.02 [−0.06, 0.10] (n.s.) on NIQ, and the paper now says so. The random-pick baseline (0.44) is useful. Dollar deltas are still missing, which is minor. |
| **W6** (MAJOR) No latency | **UNRESOLVED, accepted as a limitation** | §6 says latency is not measured. For a CVPR paper whose claim is fidelity at a given token budget, I accept this. A one-line median rendering time beside the cost figures would help. |
| **W7** (MAJOR) Deployment risks | **PARTIALLY_RESOLVED** | §6 now names ASCII-only input, billing exceptions (Gemini ≤32K, Qwen 16K/5 px, Llama), and the bypassing of safety filters. There is no billing-sensitivity analysis and no multilingual pilot. As a limitation this is acceptable. |
| **W8** (MINOR) Router calibration | **PARTIALLY_RESOLVED** | τ is now chosen by per-reader 2-fold CV (median 0.3), and the frontier is labelled in-sample (App. D). Routing is demoted to the appendix. τ is still not conditioned on the reader and still ignores the comprehension gap. §6 concedes the latter. |
| **W9** (MINOR) Multiplicity | **RESOLVED** | Tab. 2 adds a reader+item cluster bootstrap with Holm correction, and all means use one fixed set of five readers. |
| **W10** (MINOR) Output/reasoning tokens left out of cost | **UNRESOLVED** | §4 still reports prompt tokens only. There is no response. |

**On the declined items.** Leaving out the latency, caching and LLMLingua experiments is defensible at CVPR now that the claim is limited to "where pixels go within a fixed image budget". It is only defensible if the paper stops presenting cacheability as an advantage it has demonstrated (N2).

## 2) New issues

**N1 (MAJOR): the long-context K vs. X cost claim rests on a copying task.**
- *Where:* Contribution bullet 4 ("at 64K–128K characters they cost 30% fewer billed tokens at equal recall") and §5.5 ("X matches K on multi-key recall (0.99/0.97 vs. 0.94/0.96) at 31%/29% fewer billed tokens").
- *Problem:* `analysis_rescore.json` (rv2_c64k/c128k_multikey) gives gin=1.0 and dump=1.0 for every reader. Exact-set scores are about 0, and the K F1 is 0.31–0.50. The paper says this regime "measures copying rather than reading", yet uses it for the headline long-context claim. The token saving is real, because S's image is smaller. "Equal recall" here only means that both arms copy the list.
- *Fix:* Report precision-aware F1 and exact scores for this comparison, or restate the claim as "the allocated image makes the anchor prompt 29–31% cheaper". Do not imply equal reading quality.

**N2 (MINOR): the cacheability claim goes beyond the evidence.**
- *Where:* §1 ¶4 and §2 ¶1.
- *Fix:* Change the wording to "query-independent (a prerequisite for caching, not evaluated)". Alternatively, note in App. A that anchors placed after the question would break prefix caching.

**N3 (MINOR): the five-reader policy is applied inconsistently.**
- *Where:* The Fig. 5 caption ("recall averages six readers") and Tab. 8 include Claude. This contradicts §4 ("All means … use the five readers other than Claude") and RM-7.
- *Fix:* Recompute Fig. 5 on the five readers, or state this exception explicitly.

**N4 (MINOR): cost rows are averaged over a different reader set than the accuracy rows.**
- *Where:* Tab. 4 and Tab. 3. In Tab. 4 the "Billed tokens" row averages four readers (MiniMax does not report usage), but the caption does not say so. Tab. 3 does say it.
- *Fix:* Add the same note to the caption of Tab. 4.

## 3) Criterion judgements

- **Novelty: PARTLY_MEETS → MEETS (narrowed).** The contribution is now honestly limited to budget-constrained allocation. AGAR is correctly positioned as needing white-box access and depending on the query.
- **Technical soundness: MEETS, with N1.** The B (box) control, the detector-independent NIQ, and the milder-budget boundary (S−U is n.s. at 10 px) make the causal story credible, and the limits are stated.
- **Experimental validation: PARTLY_MEETS.** It is sufficient for the allocation claim. The serving-level comparisons (caching, text compression, latency) are absent but disclosed.
- **Clarity: MEETS.** The abstract, the contributions and Tab. 2 now quote consistent pooled numbers. The main body fits in 8 pages.
- **Significance: PARTLY_MEETS.** The method is useful where budgets are dense and documents contain identifiers but do not consist of them. The persistent 0.15–0.33 F1 gap to text limits it to cost-dominated settings, and the paper now says so.

## 4) Recommendation: **Minor revision**

Residual changes:
1. N1: report F1/exact scores for the K vs. X comparison at 64K–128K, or reword the contribution bullet and §5.5.
2. N2: soften the cacheability wording in §1 and §2.
3. N3/N4: make the reader-set statements consistent in Fig. 5, Tab. 8 and Tab. 4.
4. W10: add one sentence on output and reasoning tokens. Ideally also give dollar figures for one reader.
