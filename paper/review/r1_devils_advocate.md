# R1 Devil's Advocate Review: "Spend Pixels Where It Hurts: Hazard-Aware Rendering"

## 1) Strongest Counter-Argument

The paper sells a four-step method (Detect, Allocate, Anchor, Route), but three of those steps and the first contribution (verbatim corruption is concentrated in high-entropy strings and is silent) already appear in the work the project started from, *Render or Retain* (ref/main.pdf; thoughts/01_research_questions.md:3). That paper uses regex plus windowed Shannon entropy with the same ≥3.5-bit threshold, an exact-anchor sidecar, and density-based routing to text. The submission never cites it. Once those steps are credited, only **Allocate** is new, and the evidence that Allocate adds value over the prior pipeline is thin. Anchors on the uniform image (K) already reach 0.97/0.95 recall for +5% tokens (tab/baselines.tex). X−K is +0.06 at 6 px with 3/15 cells significant (uncorrected), +0.02 on natural identifiers (0.76 vs 0.74, tab/niq.tex), −0.022 on LongBench QA, all n.s. (decision log l.230), and significant in 1/6 readers at k=16. What remains is a 9–11% cost saving. Choosing a denser uniform base size for K gets about the same saving: K at 5 px costs 823 billed tokens for 0.97 recall, while X at 6 px costs 881 for 0.98 on the same readers. The headline gains (+0.45–0.49, +0.57) are measured against uniform rendering without anchors, at densities where 4 of 6 readers score about 0.00. That baseline is weaker than the one the authors' own prior pipeline would supply. K is also never run at 32K–128K, which is where the abstract's main number comes from. Stated simply: the paper is a modest, mostly cost-side refinement of an uncited pipeline, framed as a new method.

## 2) Issue List

**C1. CRITICAL: novelty / attribution.** *Location:* Sec. 1 contributions 1, 3, 4; Sec. 2 ("None of these signals captures..."); Sec. 3.2/3.4/3.5. *Problem:* Render or Retain (ref/main.pdf, abstract and Sec. 3.3) already has the entropy detector (3.5 bits), selective exact anchors, density routing, and the "silent corruption concentrates in high-entropy spans" finding. None of it is cited. The decision log even describes the router as "R-or-R style" (README l.32; decision log l.220). If the prior work is the authors' own, it still has to be cited in the third person. *Resolve:* Cite it. Narrow the claimed novelty to budget-constrained allocation. Rename the K and routed-K arms as the prior-work baseline, and make X vs. that baseline the headline result.

**M1. MAJOR: evidence / baseline choice.** *Location:* abstract; Sec. 5.1–5.2; Fig. 3. *Problem:* The headline numbers are S vs A. The fair baseline is K, and K is absent from the length study (Fig. 3 shows only A/S/T; decision log l.193). X's cost advantage over K disappears if K's base size is tuned (K@5 px: 823 tokens, 0.97). *Resolve:* Run K and X at 32K–128K. Report X vs K on a recall–cost frontier with s0 swept for both. Put X−K in the abstract.

**M2. MAJOR: selective reporting / so-what.** *Location:* Sec. 5.5, tab/longbench.tex; Sec. 5.6 corpus profile; abstract's "becomes usable." *Problem:* The plain-text arm was run on LongBench, and uniform rendering lost on average 0.18 F1 to text. Only Claude was near parity; Llama lost −0.32 and MiniMax −0.32 on HotpotQA (analysis_longbench.txt, lb_s6_* rows; decision log l.165). Table 4 leaves T out, so "no loss" is measured against an already-degraded image baseline. The router then sends 95–100% of prose documents to images (Sec. 5.6) using a rule that accounts only for identifier cost and ignores this comprehension gap. *Resolve:* Add T to Table 4. State the image–text QA gap. Either restrict the "usable" claim to strong readers or add reader capability to the router.

**M3. MAJOR: circular evaluation.** *Location:* Sec. 5.4; App. "Natural-Identifier Questions." *Problem:* Every natural target is required to be "a word flagged by the detector." The set therefore only measures cases where detection succeeds. The real-world failure mode, a missed hazard that gets shrunk with the prose in a document where other strings are flagged, is acknowledged but never measured (Sec. 5.6, detector paragraph). *Resolve:* Build targets with a detector-independent definition, for example human- or LLM-labeled "must-copy" strings, short codes, names, or 4-digit IDs. Report detector recall and the recall of missed targets under S/X vs A.

**M4. MAJOR: alternative explanation / mechanism.** *Location:* Sec. 1 ("a single misread glyph"); Sec. 3.3 lexmax rationale; R ablation. *Problem:* Under A, the weak readers' failures are almost all total misses, not near-misses. For example, Qwen and Llama at 5 px have recall 0.00 with silent rate 0.00–0.04 (analysis_ruler.txt, rbase_s5_*). S *raises* near-misses on UUIDs (Llama single_3 at 5 px: silent 0.00 to 0.60; MiniMax at 6 px: 0.04 to 0.54). On the archetypal hazard, a single UUID, S reaches only 0.08–0.20 recall for 4/6 readers at 5 px and 0.12–0.16 for 3/6 at 6 px. The 0.66 mean is driven by 7-digit numbers. Enlarged needles are also visually salient, and in NIAH salience points straight at the answer. The R ablation (random words enlarged, needles small) cannot tell "easier to find" apart from "easier to read." *Resolve:* Add a salience-only control (needles boxed or bolded at prose size) and a legibility-only control (needles enlarged and all flagged distractors enlarged too). Report results per task, and qualify the "misread glyph" story.

**M5. MAJOR: generalization / operating point.** *Location:* Sec. 4 Arms; Tab. 1. *Problem:* All long-context results use s0 ∈ {5,6} px, roughly 21–32 chars/vtok, where uniform recall is ≤0.11 for 4 readers. The short-document study shows the gain is an inverted U that vanishes at milder densities (App. short, Fig. phase). The large deltas are partly a consequence of choosing the floor. *Resolve:* Add at least one long-context budget where A is reasonable (e.g., 8–10 px) and report where S/X still help.

**m1. MINOR: statistics.** "Significant in k of n cells" with uncorrected per-cell 95% bootstrap CIs at N=20–25. For example, 3/15 for X−K is close to the false-positive rate. *Resolve:* Add a pooled mixed-effects or sign-flip test per comparison, or apply Holm correction.

**m2. MINOR: reader subsets.** Claude is missing from R and X (Tab. 1), from the density plain-text arm, and from the detector ablation. MiniMax is missing from costs. Means are computed over different reader sets across claims. *Resolve:* Use one consistent reader set per headline, or flag each subset inline.

**m3. MINOR: router evaluation.** The τ frontier and the per-density numbers are in-sample (App. Router threshold). In the sweep, r is close to a monotone function of k, so routing reduces to a k-threshold. *Resolve:* Evaluate the fixed τ=0.3 on the natural-identifier set or on real corpora with model calls.

**m4. MINOR: cost realism.** Billing depends on the provider (Llama ignores image size; Gemini tiles), and plain-text prompt caching is not considered, even though caching can cut repeated-context text cost by about 10×. *Resolve:* Discuss caching parity, since the paper itself argues renders are cacheable.

## 3) Ignored Alternative Explanations / Paths

- Salience rather than legibility as the cause of S's NIAH gain (M4).
- K with a denser s0 as a simpler path to the same cost (M1).
- Text-only extraction (anchors with no image), or text for flagged lines only, as a cheaper hybrid.
- Check-and-retry, which the prior pipeline included, would turn the residual silent errors that S does not reduce into detected failures. The paper's own limitation notes that allocation does not reduce near-misses.
- Rendering at higher contrast or with a different font for flagged spans only (no size change), which would cost no budget.

## 4) Missing Stakeholder Perspectives

- **Downstream consumers of identifiers:** even X trails text by 0.21 on natural identifiers for weak readers, and its errors are still silent. Nothing tells the user which answers to trust.
- **Practitioners with prompt caching or latency constraints:** the cost case assumes uncached, per-call text billing.
- **Users of non-English or code-heavy content:** the evaluation is ASCII only (non-ASCII is replaced by "?"), and code and logs are routed away rather than served.
- **Providers:** the vision-token formula (Eq. 1) follows the Qwen2-VL convention. Tiling changes could erase the savings.

## 5) Observations (non-defects)

- The first natural-identifier set was discarded because of artifacts that favored the authors' arms, and this is disclosed (App. niq; decision log l.268). That is good practice.
- The LongBench S/X evaluation used samples drawn after the detector was tightened (decision log l.179). The detector tightening itself is reported as a negative result.
- The random-enlargement ablation was rerun with length matching after a bug, and its conclusion did not change (decision log l.275). The disclosure is honest.
- The U and Z baselines are reasonable training-free stand-ins, and S beats them clearly. The numbers I checked in Tab. 1 and Tab. NIQ match analysis_ruler.txt.
- Costs are provider-billed tokens rather than pixels.
- The detector ablation shows correctly that missed hazards degrade S/X only back to the uniform baseline.

## 6) Overall

The empirical finding that targeted enlargement beats uniform, font-searched, and downsampled rendering at equal budget holds up. The paper's core novelty and practical-value claims do not hold in their current form. The detector, anchors, and router are prior (uncited) work. Allocation adds little accuracy over anchors and roughly 10% cost, which a denser K appears to match. The "usable optical compression" conclusion leaves out a 0.18 F1 comprehension gap to text. The core claim survives only if it is reframed as an incremental allocation step on top of credited prior work and evaluated against K at matched cost.
