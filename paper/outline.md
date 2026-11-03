# Outline — Spend Pixels Where It Hurts: Hazard-Aware Rendering for Optical Long-Context Compression

Venue: CVPR 2027 (review, anonymous). Main body ≤ 8 pages incl. figures/tables. References + LLM Usage Statement extra. Appendix after references.
Numbers: every figure/table is generated from `paper/data/numbers.json` (built by `paper/data/extract_numbers.py` from `thoughts/exp/real/analysis_*`).

## Abstract (five-sentence rule, ~180 words)
1. Context: rendering long text into images lets VLMs read it with 3–8× fewer tokens.
2. Problem (structural): uniform rendering allocates resolution independently of content, while the risk of silent verbatim corruption is concentrated in a few high-entropy spans (IDs, hashes); recall of such spans collapses and keeps falling with context length.
3. Method: a training-free, black-box renderer that (i) flags hazardous spans from the text, (ii) reallocates glyph size inside the same vision-token budget, (iii) spends the saved budget on a verbatim sidecar of the flagged strings, and (iv) routes hazard-dense documents back to text.
4. Results: 6 commercial/open VLMs; RULER 16K–128K; +0.45–0.49 recall at equal budget (46/54 cells significant); never worse than two uniform baselines (0/72 cells); near-text recall at ~0.2× text cost on sparse documents; no QA loss on LongBench (0/12 cells).
5. Closing: content-aware allocation, not more pixels, is what verbatim fidelity needs.

## 1 Introduction (~1.1 page incl. Fig. 1)
- P1 field: optical context compression (DeepSeek-OCR, Glyph, text-as-pixels) — why it matters (cost of long contexts).
- P2 existing work: uniform rendering configs; visual token pruning (training-free, vision-side); text-side prompt compression; all allocate by visual or textual saliency, none by verbatim risk.
- P3 gap (specific): (a) failures concentrate on high-entropy strings; (b) they are silent (wrong but plausible, model does not abstain); (c) they worsen with length (A recall 0.20→0.13, 32K→128K); (d) the renderer — which we control — already knows where these strings are, but uniform rendering ignores it; vision-side pruning cannot see the text.
- P4 our approach (Fig. 2 preview): detector → allocator → anchors paid by savings → density router.
- P5 contributions (3–4 bullets, verifiable).
- Fig. 1 (teaser): same 32K document; left uniform 6px (UUID unreadable, wrong answer), right hazard-aware (UUID at 12px, correct); bottom strip: recall vs context length A vs S (mean of 6 readers) + token cost vs text.

## 2 Related Work (~0.6 page; categorized, each ends with positioning)
- 2.1 Optical / visual-text context compression (DeepSeek-OCR, DeepSeek-OCR 2, Glyph, Text-or-Pixels, PIXEL, CLIPPO, Pix2Struct, "(bad) autoencoding" critique). Relation: we keep their premise, change the allocation inside the image; training-free & black-box.
- 2.2 Training-free visual token reduction (FastV, SparseVLM, VisionZip, PruMerge, ToMe, recent 2026 pruning). Contrast: they decide from visual features after encoding; we decide before rendering from the text, which is where verbatim risk is observable; text-dense failure (FCoT-VL).
- 2.3 Text-side and KV compression (LLMLingua family, Selective Context, gist/ICAE, H2O/SnapKV/StreamingLLM). Complement: they drop tokens; we never drop text, only resize it.
- 2.4 Long-context & text-rich evaluation (RULER, LongBench, Lost-in-the-middle, OCRBench, MMLongBench-Doc); dynamic-resolution VLMs (Qwen2-VL, InternVL).

## 3 Method (~1.4 page incl. Fig. 2, Alg. 1 optional)
- 3.1 Problem formulation: document x (characters), renderer R_θ(x)→ pages; budget B in vision tokens; v(I)=Σ⌈w/28⌉⌈h/28⌉; hazard set H(x) ⊂ tokens; objective: maximize verbatim fidelity on H subject to v ≤ B (budget of uniform rendering at size s_0), without dropping text.
- 3.2 Hazard detector (text-side, label-free): regex families (hex≥8, digits≥5, paths, IPs, digests) + entropy rule on letter–digit tokens; deliberately excludes 4-digit numbers (years). Fail-safe property: unflagged text is rendered as in the uniform baseline.
- 3.3 Budget-constrained size allocation (S): prose hard char-wrapped at s_lo, flagged tokens unbroken at s_hi; lexicographic search (max s_hi, then max s_lo) subject to v ≤ B; 1-px leading fallback; pagination at blank rows. Why: few spans, large marginal gain per pixel (link to phase diagram).
- 3.4 Anchor sidecar paid by savings (X): append verbatim flagged strings as text; S frees 11–28% of the vision budget, which pays for the sidecar at low density.
- 3.5 Density router: r = anchor tokens / S vision tokens, computable before any model call; r ≤ τ → X else plain text; τ chosen on held-out items.

## 4 Experimental Setup (~0.6 page)
- Readers: 6 VLMs via black-box APIs (Claude Sonnet 5.5, Gemini 3.5 Flash-Lite, GPT-6 Luna, Qwen3-VL-235B, Llama 4 Maverick, MiniMax-M3); one stateless call per item; temperature 0; costs = provider-billed prompt tokens.
- Tasks: RULER NIAH single_3 / multikey_1 / multivalue (Paul Graham haystack; 16K chars at 5px and 6px; 32K/64K/128K at 6px), hazard-density sweep (k=1…256 needles, 32K), LongBench multifieldqa_en + hotpotqa (≤40K chars, held-out samples).
- Arms: A uniform, U best uniform font/size search, Z render-large-then-downsample, K anchors on A, S ours, X ours+anchors, T plain text.
- Metrics: RULER recall (string_match_all), LongBench qa_f1; paired bootstrap 95% CI (10k) over items; significance = CI excludes 0.

## 5 Results (~3.0 pages)
- 5.1 Main comparison (Table 1): 16K, both densities, 6 readers × arms A/U/Z/S/K with billed tokens. Read: S ≫ A,U,Z at equal or lower cost; K higher recall at +5% cost → motivates X.
- 5.2 Scaling with context length (Fig. 3): A degrades 0.20→0.13; S flat ≈0.63; S cheaper than A by 15–28% and than text by 5.4–7.6×.
- 5.3 Hazard density and routing (Fig. 4): recall/cost vs k for A/S/K/X; X best for k≤16 (k=4: 0.99 at −13% vs A, −20% vs K; k=16: +0.10 over K); all image arms fail for k≥64; routing frontier route-X dominates route-K at every τ.
- 5.4 Does reallocation hurt comprehension? (Table 2): LongBench held-out, A/S/K/X; X−A +0.009, 0/12 significantly negative; earlier global-detector variant small cost → motivates strict detector (pointer to App.).
- 5.5 Analysis: detector ablation (Table 3: regex≈oracle; missed hazards degrade to uniform, never below); where real documents fall (real-corpus r distribution: prose docs 0.19–0.27× text cost, code/logs routed to text); reader strength (strong readers tolerate higher density; phase diagram in App.).

## 6 Limitations and Conclusion (~0.35 page)
- Synthetic needles dominate the fidelity evaluation; LongBench measures harm not benefit; no white-box analysis; vision-token formula is one provider's; detector is regex-based (fail-safe but recall-bounded); silent-error rate itself not reduced by S alone (only anchors remove it).

## Appendix (after references)
A Implementation details (renderer, fonts, pagination, detector regexes, prompts, token formula, routing τ selection)
B Full per-reader tables (Table 1/2/3 per reader; length scaling per reader)
C Short-context mechanism study (synthetic + real manifests, density phase diagram E2, prose probes, silent errors and "[unreadable]" prompt, cross-image contamination of subagent readers)
D Negative results: substring-level enlargement, prose line spacing, M-local, prose floor
E Real-corpus density profile (full table)
F Additional reader: Claude via subagents (held-out routing)
G Rendering examples
H Reproducibility, data, and ethics statements
