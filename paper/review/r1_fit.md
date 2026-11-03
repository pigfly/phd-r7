# R1 Journal-Fit Review (Area Chair perspective)

## 1. Summary
The paper argues that optical long-context compression (rendering text into images for a VLM) fails mainly on high-entropy strings such as UUIDs, hashes and long numbers, and that these failures are silent and get worse with length. It proposes Hazard-Aware Rendering (HAR), a training-free, query-independent pipeline. Regex/entropy rules flag hazardous strings. The renderer draws them at a larger size and shrinks the prose within the vision-token budget of uniform rendering, appends the flagged strings verbatim as text ("anchors"), and routes identifier-dense documents to plain text. Six black-box VLMs are evaluated on re-implemented RULER needles (16K-128K characters), a density sweep, 60 natural-identifier questions built from LongBench, and LongBench QA F1. Allocation alone adds +0.42 to +0.57 needle recall. The full method raises natural-identifier recall from 0.23 to 0.76 at about 0.2x the plain-text cost.

## 2. Criteria committed (written before detailed reading)
1. A vision contribution, not only a prompting trick: the gain must come from a visual or representational property, and the paper must show that it does.
2. A clear delta over DeepSeek-OCR, Glyph, FocusVTC, SEER and training-free pruning, with at least one head-to-head comparison or a principled reason why none is possible.
3. Controlled baselines that isolate the mechanism (matched-cost and matched-length controls).
4. Standard or well-justified benchmarks, with uncertainty estimates.
5. Reproducibility: pinned model versions, and at least one locally run open model; claims must not rest on drifting APIs.
6. Claims scoped to the evidence and to 8 pages; limitations stated honestly.
7. Usefulness to the efficient-MLLM / document-AI audience.

## 3. Strengths
- **The diagnosis is clear and useful** (Sec. 5.1, Tab. 1, Fig. 3). Uniform rendering at 21-32 chars/vtoken recovers 9-28% of needles, and recall falls with length (0.20 to 0.13). About 1 in 8 answers is a well-formed near-miss.
- **The R ablation is well designed** (Tab. 1). Enlarging random words, matched in length, gives 0.10 vs 0.66/0.70 for S. Targeting, not layout change, drives the gain.
- **The detector ablation is honest** (Sec. 5.6, Tab. 6). The oracle detector gives the same result on detectable needle types. Undetected needles fall back to uniform rendering.
- **Costs are billed tokens, not pixels** (Fig. 3b), and billing exceptions are disclosed (Sec. 6).
- **Negative results and a discarded dataset version are disclosed** (App. D, E).

## 4. Weaknesses

**W1 (CRITICAL): the vision contribution is not shown to beat a text-side baseline at matched cost.** Location: Tab. 1, Tab. 2, Fig. 4.
- *What is wrong.* Anchors on the uniform image (K) already reach 0.97/0.95 (Tab. 1) and 0.74 on natural identifiers (Tab. 2). X reaches 0.98/1.00 and 0.76. X beats K significantly in only 3/15 cells at 6 px and in 1/6 readers at k=16. All comparisons hold the base size s0 fixed. Yet K at 5 px (0.97, 823 tokens) is already cheaper than X at 6 px (881 tokens), although on different reader sets.
- *Why it matters for CVPR.* Without this, the effective mechanism is "grep identifiers and paste them into the prompt", which is a prompt-side trick. The pixel allocation would then contribute only about a 10% cost saving.
- *Fix.* Plot a recall-vs-billed-token frontier for K and X across s0 ∈ {4, 5, 6, 7} px on one fixed reader set, for both RULER and natural identifiers. Show where X strictly dominates.

**W2 (MAJOR): no experiments with actual optical compressors or the closest adaptive methods.** Location: Sec. 2, Sec. 4.
- *What is wrong.* The paper positions itself against DeepSeek-OCR, Glyph, FocusVTC and SEER, but runs none of them. U and Z are the authors' own stand-ins. Glyph and DeepSeek-OCR have open weights and are exactly the readers the method claims to serve. The claim that pruning (FastV, VisionZip) is "orthogonal" is never tested.
- *Why it matters.* Trained compressors may already read 6 px glyphs robustly, or mixed glyph sizes may fall outside their training distribution.
- *Fix.* Evaluate HAR on Glyph and DeepSeek-OCR at their native ratios. Add one open VLM with VisionZip/FastV applied to HAR images.

**W3 (MAJOR): the evaluation is black-box only and hard to reproduce.** Location: Sec. 4, App. "Compute and cost".
- *What is wrong.* Readers are named only by marketing names ("GPT-6 Luna"), with no snapshot IDs. Qwen3-VL and Llama were served through third-party APIs with unknown preprocessing. The reader set changes across tables: Claude is absent from R and X in Tab. 1 and from all of Tab. 2, yet it is the Fig. 1 example. Eq. (1) is Qwen accounting applied to every provider. There is no white-box analysis (Sec. 6 concedes this).
- *Why it matters.* Provider-side resizing can silently change the effective glyph size, which is the very quantity the method controls.
- *Fix.* Pin snapshot IDs. Run one open model locally, with fixed preprocessing, on every table. Use one consistent reader set. Add a small patch- or attention-level analysis.

**W4 (MAJOR): the fidelity evidence is close to circular, and the natural set is small.** Location: Sec. 3.2, Sec. 5.4, App. E.
- *What is wrong.* RULER needle values are exactly what the detector was written to catch. The natural set is 60 auto-built questions, one earlier version was discarded, and X trails text by 0.21. Missed hazards in documents where other strings are flagged (the harmful case) are never tested.
- *Fix.* Use a larger, independently sourced identifier benchmark. Add a test that mixes detected and undetected hazards.

**W5 (MAJOR): "no comprehension loss" is measured against an already-lossy baseline.** Location: Tab. 3.
- *What is wrong.* F1 (0.35/0.58) is compared with uniform rendering only. Plain-text F1 is not reported, and only two tasks at ≤40K characters are used, while cost claims extend to 128K.
- *Fix.* Add T to Tab. 3 and a long-context comprehension task.

**W6 (MINOR): headline ranges are inconsistent.** The abstract gives 0.45-0.49 and the contributions 0.42-0.57. The "63 of 72" count pools budgets and baselines without saying so.

**W7 (MINOR): routing is partly in-sample.** τ and the Fig. 4c frontier come from the same synthetic sweep (App. A). The held-out reader has N=10 per cell and estimated costs.

**W8 (MINOR): the conclusions overreach.** "Silent" errors rest on a one-reader abstention test. "Optical compression thus becomes usable" ignores the 0.21 gap to text and the unchanged near-miss rate under S (Sec. 6).

## 5. Questions for the authors
1. How does X at 6 px compare with K at 4-5 px at matched billed tokens, on identical readers?
2. Does HAR help or hurt Glyph and DeepSeek-OCR?
3. What are the snapshot IDs? Does any provider downscale large images?
4. What is plain-text F1 in Tab. 3?
5. Why is Claude excluded from X/R and from Tab. 2?

## 6. Criterion judgements
- **Novelty: PARTLY_MEETS.** Text-aware glyph allocation before encoding is new. But the mechanism is regex plus two font sizes, and most of the accuracy comes from text anchors.
- **Technical soundness: PARTLY_MEETS.** The budget constraint, paired bootstrap and R control are sound. There are no cost-matched comparisons and reader sets are inconsistent.
- **Experimental validation: PARTLY_MEETS.** Evidence is synthetic needles plus 60 natural items, with no trained compressors, no text reference for QA, and black-box readers only.
- **Clarity: MEETS.** Arms and the method are well defined, and limitations are explicit.
- **Significance to CV: PARTLY_MEETS.** The diagnosis matters to document AI. A vision contribution, as distinct from a prompt-side fix, is not shown (W1).

## 7. Recommendation: Major Revision (borderline Reject as submitted)
The changes that would most change my view:
1. A cost-matched frontier showing that S/X strictly dominate denser uniform rendering plus anchors (K) on one fixed reader set (W1).
2. Results on Glyph and/or DeepSeek-OCR and on a locally run open VLM with pinned preprocessing (W2, W3).
3. A larger, independent natural-identifier set and a plain-text comprehension reference (W4, W5).
