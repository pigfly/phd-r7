# Reviewer 3 (Cross-disciplinary: ML systems / serving cost)

## 1) Summary
The paper proposes Hazard-Aware Rendering (HAR), a training-free renderer for optical context compression. It flags high-entropy strings with regexes (Detect), draws them larger and prose smaller within the uniform-rendering vision-token budget (Allocate), uses the tokens saved to append verbatim text copies called "anchors" (Anchor), and sends identifier-dense documents back to plain text with a pre-call ratio (Route). Across six black-box VLMs, allocation alone raises RULER needle recall over uniform rendering by about 0.42-0.57 at equal or lower billed-token cost. Allocation plus anchors (X) raises recall of naturally occurring identifiers from 0.23 to 0.76 at about 0.2x the plain-text cost. The idea is simple, cheap to deploy, and the paper is careful about statistics. As a practitioner, though, I find the end-to-end case incomplete. The comparisons are almost all image-versus-image. Plain text is shown only for verbatim recall. The practical alternatives a serving team would actually use (prompt caching, text-side compression, retrieval) are missing.

## 2) Criteria committed (before detailed reading)
1. Real cost: provider-billed tokens and dollars, per provider, not proxy counts.
2. Comparison against simple practical alternatives: plain text, text-side compression (LLMLingua family), retrieval/truncation, prompt caching.
3. Latency and cacheability.
4. Deployment risks: billing-rule changes, non-ASCII/multilingual text, tokenizer differences, safety filters and injection.
5. Whether the router is usable as is: inputs, calibration, failure modes.
6. Statistical rigor and reproducibility.

## 3) Strengths
- **Costs are billed tokens, not pixel proxies** (Sec. 4, Readers; Eq. 1 used only for budgets). The limitations section reports where savings fail to hold (Gemini at ≤32K, Llama billing that ignores image size). Systems papers rarely give this level of honesty about billing.
- **Strong controls.** The random-word enlargement arm R, matched on occurrence length (Tab. 1), shows that the targeting matters (S − R ≈ 0.55). The oracle-detector test (Tab. detector) separates detector recall from allocation.
- **The router is computable before any model call** (Eq. 3), and it is profiled on real corpora without model calls (Tab. app_corpora). Code, logs, and manifests are routed to text. This is a useful and honest scoping result.
- **Rendering is query-independent** (Sec. 2), so in principle the rendered document can be reused across queries.
- **Low CPU overhead** (about 1-4 s for 32K-128K characters, unoptimized), and the full experimental spend was about $51, which makes the work reproducible.

## 4) Weaknesses

**W1 (CRITICAL). The comprehension cost of optical compression versus plain text is not reported, although the evidence file contains it.** Location: Sec. 5.6, Tab. longbench, abstract ("no significant loss in any of 12 reader-task cells"). The claim of no loss is relative to *uniform rendering*. However, `data/numbers.json` (`longbench_lb_text`, a separate LongBench sample) includes a plain-text arm. Uniform images average F1 0.56 vs. 0.74 for text on HotpotQA and 0.32 vs. 0.50 on MultiFieldQA. The A−T CI excludes zero in 9 of 12 cells (e.g., Llama HotpotQA −0.32, Qwen MFQA −0.24). Why it matters: a deployer compares against text, not against uniform images. A loss of about 0.18 F1 at about 0.2x cost is a trade-off that has to be stated. Fix: add T (and its billed tokens) to Tab. longbench. Qualify the abstract and the "0.2x plain-text cost" framing with the accuracy given up on ordinary QA.

**W2 (MAJOR). There is no end-to-end comparison against practical non-optical alternatives.** Location: Secs. 4-5 (arms A/U/Z/R/S/K/X/T only). A serving engineer facing a 128K document would first consider (a) prompt caching of the plain-text prefix, (b) LLMLingua-2/LongLLMLingua-style compression with a "do not drop flagged strings" constraint, and (c) BM25/embedding retrieval of the relevant chunk. For example, Anthropic's current pricing bills cache reads at 0.05x base input for Sonnet 5.5 (one of the readers here). For multi-query workloads over a stable document, cached text could therefore beat the ~0.12-0.2x of uncached images while keeping text accuracy. Fix: add at least a text-compression baseline that preserves flagged strings verbatim, and a cost model over the number of queries per document (with and without caching) for both text and images.

**W3 (MAJOR). The cacheability claim is undermined by prompt layout and is not measured.** Location: Sec. 2 ("can be cached and reused"); App. A, Baselines. For RULER and the natural-identifier set, the anchors are appended *after the question*, so the document-dependent suffix breaks prefix caching. For LongBench they come before the question. Providers also impose a minimum cacheable prefix (512-4,096 tokens depending on model, per Anthropic docs), and a ~1K-token image may not qualify. Fix: place anchors before the question in all experiments, or show that the order does not matter. Report cache-hit billing for at least one provider.

**W4 (MAJOR). The headline full method is never evaluated at long context.** Location: Fig. scaling and Tab. app_length, which report only A, S, and T at 32K-128K. The case for optical compression is strongest at 128K, yet X and K are tested only at ≤40K. Anchor cost also grows with document length (more flagged strings). Fix: run K and X at 64K/128K and report recall and billed tokens.

**W5 (MAJOR). The marginal value over the simplest strong baseline (K) is small.** Location: Tab. 1 and Tab. niq. K (uniform image + regex anchors, no new renderer) reaches 0.97/0.95 on RULER and 0.74 on natural identifiers, against 0.98/1.00 and 0.76 for X. The main gain is about 9-11% fewer tokens and some advantage at k=16. Fix: frame X as the cost-optimized form of K and lead with this comparison. Report dollar deltas per 1M documents so readers can judge whether a custom renderer is worth maintaining.

**W6 (MAJOR). Latency is absent.** Location: no measurements of TTFT or end-to-end latency. Image encoding, multi-page uploads, and rendering (4 s on CPU at 128K, which is comparable to model TTFT) can erase the benefit in interactive serving. Fix: report p50/p95 end-to-end latency per arm and provider, including rendering time.

**W7 (MAJOR). The deployment-risk surface is unexamined.** (a) Non-ASCII is replaced by "?" (Sec. 4), and both detector and renderer are ASCII/Menlo-centric. Multilingual text, CJK (where text tokens per character, and hence the optical savings, differ greatly), and RTL scripts are untested. (b) Savings depend on each provider's current image-tokenization rule; Llama's billing already ignores image size. A sensitivity table under alternative billing rules (fixed per image, tile-based) would make the claim robust. (c) Rendered text bypasses text-side safety and prompt-injection filters. This is a security consideration that the ethics paragraph does not mention. (d) The text-cost estimate in the router, c(w) = |w|/2 + 3, assumes one tokenizer. Fix: a short multilingual pilot, a billing-sensitivity analysis, and a limitations paragraph on safety and injection.

**W8 (MINOR). Router calibration is weak.** Location: Sec. 3.5, App. A. τ is chosen on the synthetic density sweep with an arbitrary utility (recall − 0.5·cost), and the frontier in Fig. density(c) is in-sample. The router ignores reader strength, even though Sec. 5.4 shows weak readers trail text by about 0.3 on natural identifiers. Fix: a reader-conditioned τ, a utility tied to an explicit error cost, and validation on the natural-identifier set.

**W9 (MINOR). Many tests, no multiplicity correction.** N=20-25 per cell across hundreds of cells, with per-cell bootstrap CIs. Fix: add a Holm or FDR correction, or a pooled mixed-effects estimate.

**W10 (MINOR).** Output tokens and reasoning tokens (GPT-6 Luna, "minimal") are excluded from cost. Report total billed cost.

## 5) Suggested references
- LLMLingua-2 (Pan et al., 2024): a task-agnostic compressor and the natural text-side baseline.
- RECOMP (Xu et al., 2023): retrieval-and-compress baseline.
- Prompt Cache (Gim et al., MLSys 2024): modular prompt reuse, relevant to the cacheability claim.
- CacheBlend (Yao et al., 2024): KV reuse for non-prefix contexts.

```yaml suggested-references
- title: "LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression"
  id: arXiv:2403.12968
- title: "RECOMP: Improving Retrieval-Augmented LMs with Compression and Selective Augmentation"
  id: arXiv:2310.04408
- title: "Prompt Cache: Modular Attention Reuse for Low-Latency Inference"
  id: arXiv:2311.04934
- title: "CacheBlend: Fast Large Language Model Serving for RAG with Cached Knowledge Fusion"
  id: arXiv:2405.16444
```

## 6) Questions
1. Why is the plain-text LongBench run in `numbers.json` (A−T significantly negative in 9 of 12 cells) not in the paper?
2. What are recall and billed cost for K and X at 128K?
3. With anchors placed before the question, does accuracy change, and do provider caches hit on the image+anchor prefix?
4. Which tokenizer was the 0.208/0.737 tokens-per-character fit taken from? Does it transfer across the four billed readers?
5. How do the savings change in dollars, given each provider's actual image and text price per token?

## 7) Criterion judgements
- **Novelty: PARTLY_MEETS.** Text-aware, budget-constrained glyph allocation for black-box VLMs is new and clean. The anchors and the text fallback are close to standard practice (K).
- **Technical soundness: PARTLY_MEETS.** The controls are good (R, oracle detector, billed tokens). The "no loss" claim uses the wrong reference point (W1), and the router is calibrated in-sample on synthetic data.
- **Experimental validation: PARTLY_MEETS.** Six readers, paired CIs, and real-corpus profiling. X is missing at long context, and there are no text-compression, caching, or latency comparisons.
- **Clarity: MEETS.** Arms and costs are defined precisely, and the limitations are candid about billing exceptions.
- **Significance: PARTLY_MEETS.** It is useful for identifier-sparse long documents read once. Practical significance against cached or compressed text is not established.

## 8) Recommendation: Major revision
Decisive changes:
1. Report plain-text accuracy and cost on LongBench QA, and restate the cost-accuracy trade-off against text, not only against uniform images.
2. Add practical baselines and a cost model: a text compressor that preserves flagged strings, and cached plain text over multiple queries, plus latency.
3. Evaluate K and X at 64K-128K with anchors placed cache-compatibly, and add a multilingual / billing-sensitivity pilot.

Sources: [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing), [Claude prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
