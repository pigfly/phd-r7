# R2 Journal-Fit Re-review (Area Chair, Stage 3')

Materials checked: revised `main.pdf` (15 pp.; References begin on p. 8, so the main body fits within 8 pages), `sec/*.tex`, `tab/pooled.tex`, `tab/niq.tex`, `tab/longbench.tex`, `analysis_pooled.json`, `analysis_rescore.json`, and `analysis_longbench.json` (lb3, for the X−T check).

## 1. Revision response checklist

| R1 item | Status | Evidence |
|---|---|---|
| W1 (CRIT) vision contribution vs. K at matched cost | **PARTIALLY_RESOLVED** | §5.5 adds a NIQ frontier at 5/6/7 px. X reaches 0.75/0.76/0.81 at 1017/1128/1306 tokens and K reaches 0.71/0.74/0.77 at 1014/1267/1345, which matches `analysis_rescore.json`. X−K is n.s. (+0.02 [−0.06, 0.10]; Tab. 2). No RULER frontier was swept. The contribution has been honestly narrowed to Allocate, with K credited to prior work. The new box control B (−0.05 vs. A; S−B +0.53) now makes the case that the gain is legibility, which is the vision claim I asked for. The marginal value over K, however, is still only a cost saving. |
| W2 (MAJ) no trained compressor / pruning | **UNRESOLVED** | §6 names both as untested, and §2 drops "orthogonal". The editorial's minimum fallback, a comparison point from FocusVTC's published numbers, is also missing. |
| W3 (MAJ) black-box only / reproducibility | **PARTIALLY_RESOLVED** | One fixed 5-reader set is used for all means and pooled tests (§4). There are still no snapshot IDs (App.: "identified by their provider model names"), no locally run model, and Claude is reported per reader only. |
| W4 (MAJ) circular fidelity evidence | **PARTIALLY_RESOLVED** | A detector-independent NIQ set has been added (Tab. 3, §5.4). S−A is −0.01, and X−K is −0.08 with one cell significantly negative. This tests the mixed flagged/unflagged harm case I asked for, and it is reported honestly. Both sets still have only 60 auto-built items each. |
| W5 (MAJ) comprehension vs. lossy baseline | **PARTIALLY_RESOLVED** | T has been added to Tab. 4. X−T is significantly negative in 9/10 cells, by 0.15–0.33, which I verified against lb3. The abstract and conclusion now state the gap. Comprehension is still tested only at ≤40K characters. |
| W6 (MIN) headline ranges | **RESOLVED** | The abstract, contributions and Tab. 2 all use 0.55/0.43/0.48, and the Holm counts are explicit. |
| W7 (MIN) in-sample routing | **PARTIALLY_RESOLVED** | Routing is demoted to the appendix and labelled in-sample. τ was not re-selected on a new seed. |
| W8 (MIN) overreach | **RESOLVED** | "Usable" has been replaced by "safer for identifiers rather than a substitute for text" (abstract, §6). |

Attribution of `anon2026renderretain` is now adequate. The Detect step, the anchors and the routing are credited in §1, §2, §3 (l. 11, 33, 72, 80), §4, the Fig. 2 caption and the appendix, and Fig. 2 states that "Our contribution is Allocate".

## 2. New issues introduced by the revision

**N1 (MAJOR): the long-context anchor claim rests on a metric the paper itself disqualifies.** Location: §1 contribution 4 and §5.5.
- §5.5 says that multi-key recall "measures copying rather than reading". It then claims that X matches K on multi-key *recall* at 64K/128K (0.99/0.97 vs. 0.94/0.96) at 31%/29% fewer tokens.
- Under the paper's own precision-aware F1 (`rv2_c{64,128}k_multikey_1`), X is 0.40/0.36, K is 0.38/0.39, and S alone is 0.39/0.38 at 1809/3407 tokens.
- So under F1 the anchors add nothing at long context. The saving comes from allocation, not from "paying for anchors".
- *Fix:* report F1 for this comparison and restate the result. Allocation alone matches K's F1 at about 32% fewer tokens, which actually supports the narrowed contribution better.

**N2 (MINOR): two headline claims omit their condition.** Location: abstract, §6.
- "Doubles the recall of naturally occurring identifiers" holds only for *flagged* targets. On the detector-independent set the effect is −0.01.
- "Matches or slightly exceeds anchors on uniform images" also holds only for flagged targets. On unflagged targets X−K is −0.08.
- *Fix:* add "flagged" to the first claim. Add one clause noting that anchors mislead when the target is unflagged.

**N3 (MINOR): small numeric mismatches in §5.5.**
- The X−K gap at 7 px is 0.046 (0.813 vs. 0.767), so the stated range should read "0.02–0.05", not "0.02–0.04".
- At 5 px, X and K cost the same (1017 vs. 1014 tokens), so "at lower cost" in the abstract applies only at 6 and 7 px.
- B−A's upper CI bound is −0.005, but Tab. 2 prints −0.01.

**N4 (MINOR): reader count and wording inconsistencies.**
- The abstract says "five commercial and open VLMs", while §4 lists six readers.
- The "open" models were queried through third-party APIs, not run locally. The text should say so.
- §1 refers to "the same four readers" before any reader set has been defined.

**N5 (MINOR): no-loss claim lacks a margin.** "Unchanged relative to uniform rendering" on LongBench (§5.6) is stated without the non-inferiority margin that RM-7 requested. Either state a margin (e.g., −0.05 F1) and test against it, or say "no significant difference".

## 3. Criterion judgements

- **Novelty: PARTLY_MEETS.** The contribution is now honestly narrowed to budget-constrained allocation. Compared with AGAR, it differs by being black-box and query-independent, which is a real but modest difference: regex flagging plus two glyph sizes.
- **Technical soundness: MEETS.** The paper now has reader+item cluster bootstrap CIs with Holm correction, a fixed reader set, and R and B controls, and the confounds of the operating point are tested at 8/10 px. N1 is the one place where the reasoning is internally inconsistent.
- **Experimental validation: PARTLY_MEETS.** It still has no trained optical compressor, no local or white-box model, and natural sets of 60 items each. On the other hand, the boundary of the method (10 px, unflagged targets, the gap to text) is now measured and reported.
- **Clarity: MEETS.**
- **Significance to CV: PARTLY_MEETS.** The legibility mechanism (S vs. B/R/U/Z) is a genuine rendering-side finding. Its practical advantage over the prior-work anchors is mostly a 10–30% cost saving.

## 4. Recommendation: Minor Revision (borderline Accept for CVPR)

The revision does the decision-critical work. Attribution is fixed. The anchor leakage is exposed and the claims are rescored. A text reference has been added. The frontier, pooled statistics and controls are added. The method's limits are now stated where they belong. What remains is mostly a matter of scope.

Required changes:
1. Fix N1: use F1 for the 64K/128K anchor comparison and restate contribution 4.
2. Add the conditions to the claims in the abstract and conclusion (N2), and correct the numbers in N3 and N4.
3. List model snapshot/version strings where providers expose them (W3), and add one comparison point on the compression–recall axis using FocusVTC/Glyph published numbers, or an explicit scoping sentence explaining why none is comparable (W2).

Recommended but not required: an open reader run locally on Tab. 1, and a RULER K/X frontier across s0.
