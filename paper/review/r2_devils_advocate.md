# R2 Devil's Advocate Re-Review: "Spend Pixels Where It Hurts"

## 1) Status of Round-1 Issues

| ID | Status | Evidence / anchor |
|---|---|---|
| C1 novelty/attribution | **RESOLVED** | `anon2026renderretain` is cited 11 times in sec/1–3, and the prior work is described as the "direct predecessor" (sec/2). Detect, Anchor and Route are credited to it (sec/3 Overview). The contribution is narrowed to Allocate (sec/1 bullet 1). AGAR is added as the closest enlargement method. |
| M1 K baseline / frontier | **PARTIALLY_RESOLVED** | NIQ frontier at 5/6/7 px: X 0.750/0.757/0.813 at 1017/1128/1306 tokens, K 0.713/0.737/0.767 at 1014/1267/1345 (analysis_rescore.json, matches §5.5). K at long context was run only on multi-key, where the anchors contain the answer (see N2). No pooled test is reported at 5 or 7 px. |
| M2 missing T / "usable" | **RESOLVED** | T is in Tab. 4. The abstract, §5.6 and the conclusion state the 0.15–0.33 F1 gap (numbers checked). The router still ignores this gap, but sec/6 now says so. |
| M3 circular NIQ | **RESOLVED** | niq3 samples targets without the detector. It reports detector recall (1/60) and recall on missed targets (S−A −0.01 [−0.11, 0.08]). The result also shows how narrow the method's scope is. |
| M4 salience vs legibility | **PARTIALLY_RESOLVED** | Arm B was added (B−A −0.05, S−B +0.53). B is a weak salience match (N3). The per-task UUID breakdown and the qualification of the "single misread glyph" story (sec/1 l.16) were not done. Silent and near-miss rates are absent from the main text. |
| M5 operating point | **RESOLVED** | 8/10 px runs: S−A +0.38/+0.20, S−U +0.04 n.s. at 10 px. Reported as the method's boundary in the abstract and sec/6. |
| m1 statistics | **RESOLVED** | Reader+item cluster bootstrap plus Holm correction (tab/pooled.tex, analysis_pooled.json). The values I checked match. |
| m2 reader subsets | **RESOLVED** (one residual) | A fixed 5-reader set is used throughout. The App. density caption still says "recall averages six readers". |
| m3 router in-sample | **PARTIALLY_RESOLVED** | Routing is demoted and labelled in-sample (App. l.27, l.111). It was not evaluated out of sample. |
| m4 caching/billing | **PARTIALLY_RESOLVED** | Disclosed in sec/2 and sec/6. The "5.4–8.0× cheaper than text" figure (§5.2) is still stated without the caching caveat. |

## 2) Strongest Remaining Counter-Argument

After narrowing, the paper claims one thing: Allocate. Allocate's large effect appears only where detection is effectively perfect. On RULER, the needles are the *only* flagged strings in the haystack (§5.5). So S is an oracle enlargement of 1–4 strings, and the +0.43–0.55 headline measures oracle-detected targets. On natural data the effect shrinks to +0.25 when the detector flags the target. It is zero when targets are sampled independently, because the detector flags 1 of 60. The prior-work baseline also beats the contribution outright. On flagged natural identifiers, K (anchors on a uniform image) scores 0.74 and S scores 0.48 (Tab. 3). Allocation's added value on top of K is ≈0 in every pooled X−K test except one: RULER 5 px +0.005, 8/10 px −0.001 F1, 32K density −0.014 F1, 64K/128K −0.005 F1, NIQ +0.02 n.s., and NIQ detector-independent −0.08 with one Holm-significant negative cell. The decision log says as much: "X−K is ≈0 pooled". What remains is a cost saving of about 10–30%. Its long-context instance is measured with recall on multi-key, where every image arm's F1 is ≈0.38, *including S alone at 32% lower cost than X*. A practitioner who already uses the predecessor gains a modest token discount and loses accuracy whenever a target goes unflagged.

## 3) New Issues

**N1. MAJOR: abstract and conclusion generalize the natural-string result.** The abstract and the conclusion say allocation "doubles the recall of naturally occurring identifiers (0.23 to 0.48)". That holds only for *detector-flagged* targets. On detector-independent targets the gain is −0.01 (Tab. 3, Tab. 2), and neither the abstract nor the conclusion mentions this. The abstract also says X "matches or slightly exceeds anchors on uniform images". It leaves out that X−K is −0.08 and X−A is −0.09 (with Holm-significant negative cells) when the target is unflagged. *Resolve:* Write "detector-flagged identifiers" in the abstract and conclusion. Add one clause saying the gain is zero on unflagged digit strings and that anchors then hurt. Note in §5.1 that RULER needles are the only flagged strings, so S there amounts to oracle targeting.

**N2. MAJOR: the composition claim (contribution 4) rests on selectively reported metrics.**
(a) Tab. 2 reports X−K on RULER only at 6 px and only as F1 (+0.04 [0.01, 0.08], 1/15). It omits 5 px (+0.003), 8/10 px (−0.001), long_kx (−0.005) and density (−0.014), all of which are in analysis_pooled.json.
(b) "At 64K–128K they cost 30% fewer billed tokens at equal recall" uses recall on multi-key, a task §5.5 itself calls "copying rather than reading". F1 is 0.38/0.36 for X and 0.38/0.39 for K. S alone reaches 0.39/0.38 at 1809/3407 tokens, which is cheaper than X (1851/3458).
(c) "Not significant at 6 px" implies significance at 5 and 7 px, but no test is reported there. All per-reader CIs at 5 px cross zero.
(d) "0.02–0.04" understates the gap at 7 px, which is 0.046.
*Resolve:* Report every X−K row in Tab. 2. Add F1 to the long-context claim, or drop the claim. Run pooled tests at 5 and 7 px or remove the implication. State plainly that X−K ≈ 0 in accuracy and that the benefit is cost.

**N3. MINOR: the box control is confounded.** `render_box` (make_items.py l.159–179) draws a 1-px outline flush against the glyph advance and line top at 6 px. This can degrade the first and last characters, which may explain B < A. A thin box is also much less salient than a 12-px string. "The gain comes from legibility, not from pointing at the needle" is therefore stronger than the evidence supports. *Resolve:* Add padding to the box, or use a bold or high-contrast highlight, and soften the sentence.

**N4. MINOR: possible unreported runs.** `log_gen_niq3_s5.log` and `log_gen_niq3_s7.log` exist, but there are no niq3_s5 or niq3_s7 outputs and they are not reported. *Resolve:* State whether these were evaluated. If they were, report them.

**N5. MINOR: AGAR is discussed but not compared empirically.** Qwen3-VL has open weights, so an attention-guided upper bound is feasible. At minimum, the paper should clarify that its novelty over AGAR lies in query-independence and black-box access, not in enlargement itself.

## 4) Overall

The revision is honest and substantial. Attribution is fixed. Plain-text references, Holm-corrected pooled statistics, a detector-independent set, milder budgets and a salience control were all added, and the numbers I spot-checked match the JSON evidence. The narrowed core claim does survive: text-side, budget-constrained glyph allocation beats uniform rendering, font search, downsampling, random enlargement and boxing at dense budgets. It does so by a large, robust margin *when the hazardous string is detected*. Two framing problems remain. First, the "natural identifiers" result has to be qualified as covering flagged strings only (N1). Second, the composition-with-anchors contribution adds no accuracy over the predecessor's anchors and should be presented as a cost result, with every X−K row and F1 at long context reported (N2). Both fixes are textual. Verdict: **Minor-to-Major revision. The core claim survives, but contribution 4 and the abstract's natural-string sentence overclaim.**
