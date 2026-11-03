# Reviewer 2 (Domain): Hazard-Aware Rendering for Optical Long-Context Compression

## 1. Summary
The paper argues that optical context compression (rendering text to images for a VLM) spreads resolution evenly, while its errors cluster on high-entropy strings such as UUIDs, hashes and report numbers. The proposed method, HAR, is training-free. A regex/entropy detector flags such strings (Detect). They are drawn larger and prose smaller within the uniform rendering's vision-token budget (Allocate). The tokens this saves pay for verbatim text copies of the flagged strings (Anchor). Identifier-dense documents go back to plain text using a ratio computed before any model call (Route). Six black-box VLMs were tested on RULER needles at 16K–128K characters, a 60-question natural-identifier set built from LongBench, and LongBench QA. Allocation raises needle recall over uniform rendering by about 0.45, beats font/size search and render-then-downsample, and a random-word enlargement control shows the gain comes from targeting. The paper is careful and honest, but its position relative to trained optical compressors and token pruning rests on argument rather than experiment.

## 2. Criteria committed (before detailed reading)
1. Positioning against the PIXEL / Pix2Struct / DeepSeek-OCR / Glyph lineage, adaptive-resolution VTC (FocusVTC, SEER) and vision-token pruning.
2. At least one strong existing system as a baseline, or a principled argument that it does not apply.
3. Whether the rendering regime (Menlo, 5–6 px, 1008 px, character wrapping) matches real optical compressors.
4. Whether the paper teaches something about *how* VLMs read small text, beyond accuracy deltas.
5. Whether claims stay within the readers, tasks and statistics actually used.

## 3. Strengths
- **Clear, falsifiable mechanism with the right control.** Arm R enlarges random words matched in total length (Sec. 5.1). It stays at 0.10, against 0.66–0.70 for S, so "enlargement as such" cannot explain the gain. This is the ablation I would have asked for.
- **Equal-budget comparisons with costs from provider bills** (Tab. 1, Fig. 3b). Using billed tokens instead of a nominal pixel count is the right unit for black-box deployment.
- **Characterization of silent failure.** About one in eight needles comes back as a well-formed near-miss, and offering an "[unreadable]" answer does not help (App. C). This is a useful finding for the VTC community. It complements VTCBench and "Reading, Not Thinking", which report accuracy loss but say less about the *form* of errors.
- **Honest scoping.** The detector ablation (Tab. 5) shows that missed hazards fall back to uniform rendering. The corpus profile (App. F) says plainly that code and logs should go to text. A first natural-identifier set that favored the method was discarded (App. E).
- **Collateral-damage check on held-out LongBench** with paired CIs (Tab. 3).

## 4. Weaknesses

**W1 (CRITICAL). No evaluation on any actual optical compressor, and no empirical comparison with the closest adaptive-resolution work.** *Location:* Sec. 2 ¶1, Sec. 4 "Arms". *Problem:* All six readers are general-purpose VLMs. Glyph, DeepSeek-OCR and DeepSeek-OCR 2 all have public weights and are trained to read dense rendered text, yet none is used as a reader. FocusVTC (arXiv:2609.36651) also releases code, and it reports RULER at 72 DPI and about 2.9× compression. HAR is set apart from FocusVTC and SEER in a single sentence ("trained… query-dependent"), with no numbers. *Why it matters:* The motivating claim is that "existing systems decide how densely to render, but not where." A trained compressor may already resolve high-entropy glyphs at its working density, in which case HAR's gain shrinks. The failure may also persist, which would make the paper much stronger. Readers cannot currently tell which. *Fix:* (a) Run A/U/S/X with Glyph (or DeepSeek-OCR) as the reader, at its native rendering configuration and at a matched compression ratio. (b) Report FocusVTC on the same RULER items, or reproduce its compression-ratio/recall point. At minimum, place HAR on the same compression-vs-recall axes using FocusVTC's published numbers, and state explicitly why a query-dependent, tool-calling method is or is not a competitor when the cost and the "cacheable rendering" property are taken into account.

**W2 (MAJOR). The rendering regime is chosen where uniform rendering collapses, and its representativeness is not argued.** *Location:* Sec. 4, App. A. *Problem:* Glyph height of 5–6 px in monospace Menlo, with character-level wrapping that splits prose words across lines, is much harsher than Glyph's DPI-based typeset pages or DeepSeek-OCR's real document layouts. At 5 px, four of six readers get 0.00–0.02 under uniform rendering. Most of the reported "+0.45–0.57" therefore comes from moving models off a floor. Where a reader is above the floor (Gemini 0.88 at 6 px), the gain is 0.12, and App. C shows an inverted-U over density. *Why it matters:* The headline numbers depend on the regime, and practitioners using proportional fonts, word wrapping and roughly 9–10 px text may see far smaller effects. *Fix:* Add a sweep over base sizes (e.g., 6/8/10 px), with a proportional font and word wrapping, on the long-context RULER setting. Report gain against the uniform baseline's accuracy rather than only at two hand-picked budgets. Relate chars/vision-token to the compression ratios reported by Glyph and DeepSeek-OCR.

**W3 (MAJOR). The claim that token pruning is "orthogonal" is never tested, although an open reader is available.** *Location:* Sec. 2 ¶2. *Problem:* Qwen3-VL is open, and FastV, VisionZip and SparseVLM are drop-in. Pruning by attention or saliency could easily discard the patches of a small glyph run, or keep the enlarged ones preferentially. RTPrune specifically targets text-dense OCR images. *Why it matters:* Pruning is the main training-free competitor for the same budget. "Orthogonal" is an empirical claim. *Fix:* On Qwen3-VL, compare (i) uniform at a larger size, pruned to budget B, against (ii) S at B, and (iii) S combined with pruning. That is one table.

**W4 (MAJOR). Most of the headline accuracy comes from anchors, which are a trivial text-side baseline; the paper's framing understates this.** *Location:* Tab. 1, Tab. 2, abstract. *Problem:* K (uniform image + regex-extracted strings as text) already reaches 0.95–0.97 on RULER and 0.74 on natural identifiers. X adds +0.01–0.06 and saves 9–11% of tokens. The domain contribution is therefore mainly cost (allocation pays for anchors) plus routing. That is useful, but it is a different paper from "spend pixels where it hurts." *Fix:* Make K the primary baseline in the abstract and the introduction. Report X−K differences with CIs as the main result. Add the obvious hybrid baseline: delete flagged strings from the image and splice them in as text (an interleaved text–image prompt, cf. VisInContext). This tests whether pixels are needed for hazards at all.

**W5 (MAJOR). Limited insight into how VLMs read small text.** *Location:* Sec. 5.6, Limitations. *Problem:* The paper does not analyze glyph size relative to the 14/28-px patch grid, or near-miss character confusions (e.g., which hex characters get swapped, and whether errors cluster at patch boundaries). It also does not ask whether failures come from localization (finding the key) or transcription. Qwen3-VL is open, so patch-level attention or a "crop-and-read" probe is feasible. *Why it matters:* A CVPR audience expects a vision finding. The current paper is mostly a prompting/rendering recipe. *Fix:* Add a confusion analysis of near-misses, and a localization-vs-transcription split: given the correct line cropped, can the reader transcribe it?

**W6 (MINOR).** The statement that cited failures "concern the same kind of high-entropy, prior-free strings" (Sec. 2) is an interpretation, not something those papers report. Soften it.

**W7 (MINOR).** Recall uses case-insensitive substring matching (App. A), which is lenient for verbatim fidelity. Hex case errors count as correct. Report exact match as well.

**W8 (MINOR).** The extra Claude reader uses an agent interface that "may resample images" (App. H), and the main-table Claude row lacks R and X. Both make cross-reader claims uneven.

**W9 (MINOR).** The related-work section skips the OCR-free document understanding and compression lineage (Donut, DocOwl2, TextMonkey) and generative pixel LMs (PIXAR). These matter for the claim that no prior system reallocates resolution to text regions: DocOwl2 and TextMonkey compress high-resolution text images with learned, content-guided token selection.

## 5. Missing references
- **mPLUG-DocOwl2** (arXiv:2409.03420): compresses each high-resolution document page to 324 tokens. This is a direct precedent for budgeted visual text compression in OCR-free reading.
- **TextMonkey** (arXiv:2403.04473): token resampling and filtering for text-rich images. This is content-aware allocation inside the model.
- **Donut** (ECCV 2022, arXiv:2111.15664): the canonical OCR-free document transformer.
- **PIXAR** (Findings of ACL 2024, arXiv:2401.03321): a generative pixel-space LM that completes the PIXEL lineage.
- **PixelWorld** (TMLR, arXiv:2501.19339): a benchmark of text-as-pixels inputs that varies font and size, relevant to W2.

```yaml suggested-references
- title: "mPLUG-DocOwl2: High-resolution Compressing for OCR-free Multi-page Document Understanding"
  id: arXiv:2409.03420
- title: "TextMonkey: An OCR-Free Large Multimodal Model for Understanding Document"
  id: arXiv:2403.04473
- title: "OCR-free Document Understanding Transformer (Donut)"
  id: arXiv:2111.15664
- title: "PIXAR: Auto-Regressive Language Modeling in Pixel Space"
  id: arXiv:2401.03321
- title: "PixelWorld: Towards Perceiving Everything as Pixels"
  id: arXiv:2501.19339
```

## 6. Questions
1. Does S help Glyph or DeepSeek-OCR at their native settings? If not, is HAR mainly a patch for general VLMs that were never trained on dense text?
2. How do gains change at 8–10 px base size with a proportional font and word wrapping?
3. Are near-miss errors in uniform rendering localized to particular character pairs or patch positions?
4. With a matched budget on Qwen3-VL, how do uniform+VisionZip/FastV compare with S?
5. How does X compare with splicing flagged strings out of the image into interleaved text?

## 7. Criterion judgements
- **Novelty: PARTLY_MEETS.** Text-side, query-independent pixel allocation for black-box readers is new to my knowledge. However, content-aware resolution (FocusVTC, SEER, DocOwl2) and anchors (essentially extracted text) are close, and the novelty against them is argued, not shown.
- **Technical soundness: MEETS.** Paired bootstrap CIs, the random-word control, the oracle-detector ablation and honest negative results are all present.
- **Experimental validation: PARTLY_MEETS.** Six readers and three task families are tested, but there is no trained optical compressor, no pruning baseline, and only a harsh rendering regime (W1–W3).
- **Clarity: MEETS.** The paper is well organized and the arms are clearly defined. The abstract overloads numbers.
- **Significance: PARTLY_MEETS.** The finding about silent, concentrated errors is useful. Practical value over the trivial K baseline is mainly a cost reduction of about 10%.

## 8. Recommendation: **Major revision**
Decisive changes:
1. Evaluate on at least one trained optical compressor (Glyph or DeepSeek-OCR), and place HAR against FocusVTC on a common compression/recall axis (W1).
2. Add a rendering-regime sweep (base size, proportional font, word wrapping) and a pruning comparison on Qwen3-VL (W2, W3).
3. Reframe the headline around X vs. K plus routing, and add an interleaved text-splice baseline (W4).
