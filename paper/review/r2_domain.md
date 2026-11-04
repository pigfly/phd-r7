# Reviewer 2 (Domain), Round 2 Re-review: Hazard-Aware Rendering for Optical Long-Context Compression

The revision is substantive and candid. The contribution is now narrowed to *allocation* (S), anchors and routing are credited to prior work, a pooled reader+item bootstrap with Holm correction has been added (Tab. 2), and the paper states its limits (10 px boundary, the gap to plain text on LongBench, detector-independent strings). Most of my domain asks that needed a GPU or a trained compressor were declined, and the authors say so openly.

## 1. Revision response checklist

| Item | Status | Anchor / evidence |
|---|---|---|
| W1 (CRIT) No trained optical compressor; no empirical FocusVTC/SEER comparison | **UNRESOLVED** (now a scoped limitation) | Sec. 6 Limitations names Glyph and DeepSeek-OCR as "untested". Sec. 2 is better positioned, but nothing is placed on a common compression–recall axis, even using published FocusVTC/Glyph numbers, which would cost nothing. |
| W2 (MAJ) Floor regime, representativeness | **PARTIALLY_RESOLVED** | Sec. 5.3 and Tab. 2 add 8/10 px at 32K. S−A is +0.38/+0.20, and S−U is +0.04 (n.s.) at 10 px. The abstract and limitations now state this boundary, which is the right response. Still missing: a proportional font and word-wrapped prose for S at the milder sizes (App. A still uses Menlo with character wrapping), and an explicit mapping from chars/vision-token to the Glyph and DeepSeek-OCR compression ratios. |
| W3 (MAJ) Pruning "orthogonal" untested | **PARTIALLY_RESOLVED** | The overclaim is removed (Sec. 2 ¶2: "an open question that we do not test"). There is still no experiment. |
| W4 (MAJ) Anchors dominate; K should be the primary baseline | **PARTIALLY_RESOLVED** (largely addressed) | Contributions are narrowed to S. K and X are framed as prior-work baselines. Sec. 5.5 shows anchors are the answer on RULER and moves the K/X comparison to NIQ with a random-pick baseline (0.44). X−K now has CIs (Tab. 2: +0.02 n.s. natural; −0.08 detector-independent). The text-splice (interleaved) baseline is still missing. |
| W5 (MAJ) Little insight into how VLMs read small text | **PARTIALLY_RESOLVED** | Arm B (box, no enlargement; S−B = +0.53) gives a useful localization-vs-legibility split: finding the string is not the bottleneck. There is still no confusion analysis, patch-grid or crop-and-read probe (RM-13/16 declined). |
| W6 (MIN) "Same kind of strings" overreach | **RESOLVED** | Sentence removed from Sec. 2. |
| W7 (MIN) Exact-match scoring | **UNRESOLVED** | Sec. 4 still uses case-insensitive containment. Precision-aware F1 addresses a different problem (dumping). Rescoring existing logs would cost nothing. |
| W8 (MIN) Uneven Claude coverage | **RESOLVED** | Claude is excluded from every mean and pooled test (Sec. 4), and the agent-interface caveat is kept in App. H. |
| W9 / Missing refs | **PARTIALLY_RESOLVED** | DocOwl2, TextMonkey, AGAR, LensVLM, LLMLingua-2 and Prompt Cache were added. Donut, PIXAR and PixelWorld were not. PixelWorld in particular varies font and size and bears directly on W2. One clause would be enough. |

## 2. New issues

**MAJOR N1. AGAR is now acknowledged as the closest work, but there is no comparison.** *Anchor:* Sec. 2 ¶1; Sec. 5.7 (oracle detector). I verified on arXiv:2606.12898 that AGAR is a training-free, model-agnostic method. It enlarges word spans picked by middle-to-late-layer attention, then re-renders and re-infers, so it needs a first pass for each query. That makes the novelty "decide enlargement from the text rather than from attention". This is a real distinction for black-box and cacheable use, but it is narrower than the introduction's framing ("Methods that do vary resolution … read the model's attention", Sec. 1 ¶2). *Fix (no GPU needed):* (a) Present the oracle-needle arm (Tab. 5) explicitly as an upper bound for any query-dependent enlargement such as AGAR's. (b) Give AGAR's cost in the same billed-token unit (at least two passes) next to S. (c) Optionally run AGAR on a small open Qwen3-VL. At minimum, add one sentence in Sec. 5 that places AGAR on the cost/recall picture.

**MINOR N2. AGAR wording.** "mid-layer attention" (Sec. 2) should read "middle-to-late-layer attention", as in the AGAR abstract. The LensVLM description (post-trained, expands relevant compressed pages on demand via learned tools) is accurate (arXiv:2605.07019). The DocOwl2 and TextMonkey characterizations are acceptable.

**MINOR N3. Load-bearing claims rest on an unverifiable anonymous citation.** Sec. 1 ¶3 says "Prior work … showed that such silent corruption concentrates in high-entropy spans", citing `anon2026renderretain` (under review). The supplement must actually contain it. Otherwise, rephrase as a finding this paper re-confirms (App. C already supports it).

**MINOR N4. The salience control has a small confound.** B−A = −0.05 with a CI that excludes zero (Tab. 2). Box strokes take up pixels and may occlude neighbouring glyphs at 6 px. Say so, or draw the boxes in the margin or the background, before reading B as "easy to find, not easier to read".

**MINOR N5. Scope implication of the detector-independent set.** In Sec. 5.4, all image arms score 0.36–0.45 against 0.96 for text on ordinary digit-bearing tokens. This is arguably the more important domain finding: the hazard class is much broader than high-entropy strings. The introduction's "identifiers, hashes, … long numbers" framing should acknowledge that short numbers and version strings fail too and are not protected.

## 3. Criterion judgements
- **Novelty: PARTLY_MEETS.** Text-side, query-independent, black-box allocation is distinct from AGAR, LensVLM and FocusVTC. After AGAR, the margin is narrow, and it is argued rather than measured (N1).
- **Technical soundness: MEETS.** Pooled cluster bootstrap, Holm correction, a fixed reader set, the random-word and box controls, and an oracle detector.
- **Experimental validation: PARTLY_MEETS.** It is much improved (milder budgets, detector-independent targets, plain text on LongBench, K/X frontier). There is still no trained compressor or pruning baseline, and the regime is still monospace with character wrapping.
- **Clarity: MEETS.** Headline numbers are consistent across the abstract, contributions and Tab. 2.
- **Significance: PARTLY_MEETS.** The effect is large where budgets are tight and vanishes against a font search at 10 px. The value is real but concentrated in a specific regime.

## 4. Recommendation: **Minor revision** (borderline Major)
I downgrade from Major because W2 and W4 are now honestly bounded, and the claims no longer exceed the evidence. W1 remains a scoped limitation that a CVPR audience will notice. Residual changes, all doable without a GPU:
1. Place S against AGAR and FocusVTC/Glyph on one cost–recall picture, using published numbers and the oracle arm as the query-dependent upper bound (W1, N1).
2. Map chars/vision-token to the compression ratios of trained compressors, and run one proportional-font, word-wrapped point at 8 px (W2).
3. Add exact-match (case-sensitive) recall from existing logs (W7).
4. Fix the AGAR wording, cite PixelWorld, Donut and PIXAR briefly, and handle the box-arm confound and the scope wording (N2–N5).
