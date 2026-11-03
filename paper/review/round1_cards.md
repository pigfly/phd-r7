# Stage 3 — Reviewer Configuration Cards (Round 1)

Paper: "Spend Pixels Where It Hurts: Hazard-Aware Rendering for Optical Long-Context Compression" (CVPR 2027 submission, review copy)
Field analysis: primary = vision-language models / efficient multimodal inference; secondary = long-context NLP evaluation, document understanding. Paradigm: empirical method paper (training-free, black-box) with benchmark-style evaluation across commercial and open VLMs. Maturity: complete draft, 8-page main body + appendix. Target tier: CVPR main track (top venue; criteria: novelty, technical soundness, experimental validation, clarity, significance to the CV community).

## Card 1 — Journal-Fit Reviewer (internal role EIC)
- Identity: CVPR Area Chair working on efficient multimodal LLMs and document AI (token reduction, OCR-free reading).
- Focus: fit to CVPR (is this a vision contribution or an LLM-prompting trick?), novelty relative to DeepSeek-OCR, Glyph, FocusVTC, SEER and training-free token pruning; significance and audience; whether the claims match an 8-page CVPR paper.
- Preferences: values clear problem framing and convincing baselines; skeptical of black-box-only evaluations with commercial models whose versions may change.

## Card 2 — Reviewer 1 (Methodology)
- Identity: evaluation-methodology researcher for LLM/VLM benchmarks; statistics and experimental design.
- Focus: fairness of the equal-budget comparison (vision-token formula vs provider billing, page rounding), sample sizes (N=20–60 per cell), paired bootstrap and multiple comparisons, reader subsets that differ across experiments, threshold selection (cross-validated vs in-sample), synthetic needles vs natural identifiers, reproducibility with closed APIs, scoring choices (case-insensitive containment).
- Preferences: wants effect sizes with CIs, pre-specified analyses, and explicit limits on generalization.

## Card 3 — Reviewer 2 (Domain: optical context compression / document understanding)
- Identity: researcher on text-as-image language modeling and OCR-free document understanding (PIXEL / Pix2Struct / DeepSeek-OCR lineage).
- Focus: related-work coverage and positioning; whether the baselines (uniform, font search, downsampling, anchors) are the right ones versus trained adaptive-resolution methods and vision-token pruning on open models; whether the rendering choices (Menlo, 5–6 px, 1008-px width) are representative of real optical compressors; what is learned about how VLMs read small text.
- Preferences: expects comparison to at least one strong existing system or a principled argument why it is inapplicable.

## Card 4 — Reviewer 3 (Perspective: LLM systems / serving and text-side compression)
- Identity: ML-systems practitioner working on long-context serving cost (KV cache, prompt compression like LLMLingua, caching).
- Focus: practical value — real token/cost savings across providers, latency, cacheability, when to prefer text-side compression or plain text; deployment risks (provider billing changes, safety filters, multilingual/non-ASCII text, tokenizer differences); whether the router is usable in practice.
- Preferences: wants end-to-end cost–accuracy comparisons against simple practical alternatives.

## Seat 5 — Devil's Advocate (fixed, not configured)
- Challenges the core argument, detects cherry-picking, overgeneralization, and alternative explanations; produces the strongest counter-argument.
