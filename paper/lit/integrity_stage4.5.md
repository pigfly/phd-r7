# Stage 4.5 Final Integrity Verification

Verifier: independent (did not author). Date: 2026-11-05. Scope: paper/ at HEAD d981c0f (clean tree), main.pdf built 2026-11-05 07:55.

## Summary verdict: FAIL (minor; 5 number mismatches + 2 must-fix items, all fixable in < 1 h)

| Check | Denominator | Result |
|---|---|---|
| 1. Numbers, main body (abstract to conclusion, teaser, fig/method, table captions) | 97 quantitative claims | 91 VERIFIED, 4 MISMATCH, 2 UNVERIFIABLE |
| 1. Numbers, appendix (sec/X_appendix.tex + appendix tables) | 52 claims | 47 VERIFIED, 1 MISMATCH, 1 reader-set inconsistency, 3 UNVERIFIABLE/approx |
| 2. Tables regenerated | 10/10 tab/*.tex | identical (also numbers.json re-extracted byte-identical) |
| 3. Citations | 53 cited keys | 53/53 in refs.bib (4 unused bib entries); 7/7 spot-checked works described accurately (2 wording nits) |
| 4. Claim–evidence | ~40 evaluative sentences reviewed | 5 flagged (1 medium, 4 minor) |
| 5. Format | page limit / log / placeholders | PASS: conclusion ends p.8, References start p.9; 0 undefined refs/cites; 0 TODO/placeholder |
| 6. Double-blind | main.pdf text + metadata | PASS for main.pdf; 1 supplementary risk (see B2) |

Fixed reader set used for checking: the 5 non-Claude readers (Gemini 3.5 Flash-Lite, GPT-6 Luna, Qwen3-VL-235B, Llama 4 Maverick, MiniMax-M3); cost means over the 4 of them that report usage.

## Blocking / must-fix items

### M1. Length-study CI does not match the evidence
- sec/5_results.tex:37: "a pooled gain of 0.48 [0.42, 0.54]".
- analysis_pooled.json `length|S-A|recall`: pooled 0.482, ci_readers_items [0.435, 0.525], so the correct CI is **[0.43, 0.53]**. tab/pooled.tex already prints [+0.43, +0.53].
- Fix: change the text to [0.43, 0.53].

### M2. Length-study cost savings include Claude, which breaks the fixed 5-reader rule
- sec/5_results.tex:38 gives "15%, 23%, and 28% fewer billed tokens". Those are means over 5 billing readers *including Claude* (numbers.json `length_scaling[*|mean]`). Over the 4 non-Claude billing readers they are **13.4%, 23.4%, 27.0%, i.e. 13%, 23%, 27%**.
- The same number appears in sec/0_abstract.tex:7 ("up to 28%", should be **27%**) and sec/3_method.tex:71 ("15–28%", should be **13–27%**).
- Fig. 3b (fig/make_figures.py `scaling()`, line ~116) plots `ls[...|mean]["billed_*"]`, which also includes Claude.
- Fix: recompute over R5 in make_figures.py and update the three sentences, or explicitly say that cost means here include Claude. setup:L9 says all means exclude Claude, so the first fix is the consistent one.
- (The 5.4×/6.8×/8.0× vs text and the 27.1K/4.7K figures use the 4 non-Claude readers and are VERIFIED.)

### M3. tab/app_length.tex Mean row is a 6-reader mean
- The printed Mean row (0.20/0.64, 0.15/0.64, 0.13/0.62) includes Claude. The 5-reader values used in the text and in Fig. 1/3 are **A/S = 0.12/0.60, 0.08/0.57, 0.07/0.56**.
- Fix: in make_tables.py (A1 block) compute the mean over R5, or relabel the row "Mean (6 readers)".

### M4. Appendix density sweep uses six-reader means, which contradicts setup
- X_appendix.tex:100 caption ("recall averages six readers") and :104-107 (0.50/0.33/0.13, 0.39 at k=64, X 0.99 at k=4) are 6-reader means. They are disclosed, but sec/4_setup.tex:9 says "All means and pooled tests use the five readers other than Claude".
- 5-reader values: S 0.42 (k=1), 0.24 (k=16), 0.06 (k=64); K/X at k=64 0.34/0.32; X at k=4 0.98.
- Fix: either recompute, or soften setup:L9 to "All means in the main paper ..." and keep the disclosure.

### B1. Citing the prior work conflicts with the user's recorded preference (needs user confirmation)
- The user's standing memory note says: "Paper: no R-or-R citation — 论文不引用 ref/main.pdf; anchors/路由写成通用 baseline". lit/verification.md also lists R-or-R as "Excluded per instruction".
- The current manuscript cites anon2026renderretain 11 times (intro, related work, method, setup, results, Fig. 2, Tab. 1, appendix) and calls it "the direct predecessor of this work" (sec/2_related.tex:12).
- Commit 87a50ea ("cite prior work") reversed the exclusion during revision. Confirm with the user that this reversal is approved. If it is not, every anchor/routing attribution has to be rewritten as a generic baseline.

### B2. Supplementary anonymity
- The main paper and refs.bib say "anonymized copy in the supplementary material" (X_appendix.tex:152).
- ref/main.pdf, the only copy in the repo, is **not anonymized**: it shows the author names, RMIT University, and the authors' e-mail addresses.
- Fix: make sure an anonymized build is what goes into the supplement. Also consider rewording "the direct predecessor of this work" (2_related:12) to third person, e.g. "the closest prior work", so the paper does not assert shared authorship.

## Non-blocking findings

### Claim–evidence
1. **sec/6_conclusion.tex:15, "makes the anchors of prior work cheaper"** (medium). This is unconditioned, but it is false at 5 px (equal cost) and at density k=256 (X 7495 vs K 6897 billed). Fix: "cheaper wherever allocation shrinks the image", as in the abstract.
2. **sec/0_abstract.tex:10, "anchors ... as accurate on the allocated image as on a uniform one"**. The intro (1_intro:33) correctly limits this to settings with flagged targets. In the abstract it is unconditioned, yet on detector-independent targets X−K = −0.08 [−0.17, 0.01] (1 Holm-negative cell). The equivalence also rests on non-significance with CIs up to ±0.10. Fix: add "when the targets are flagged".
3. **sec/5_results.tex:101, "Prose-dominated documents are routed to images 95–100% ... 0.19–0.27×"**. This silently leaves out MultiFieldQA (75%, 0.43×; tab/app_corpora). Fix: name MFQA as the exception or say "most prose-dominated".
4. **sec/5_results.tex:60, "every image arm is equally poor (0.36–0.45)"**. X is significantly below A in 2/5 cells (tab/niq daggers). Fix: drop "equally" or say "similarly poor".
5. **sec/5_results.tex:74, "no single difference is significant (tab:pooled)"**. tab:pooled only has the 6 px natural X−K row. The 5/7 px comparisons are not reported anywhere. Fix: cite them or limit the claim to 6 px.

### Citation wording nits
- **2_related:9, DocOwl2 "token selection"**. The paper describes a learned DocCompressor guided by low-resolution global features, which is compression, not selection. TextMonkey's similarity-based token filtering does fit "selection". Fix: "learned, content-guided token compression/filtering".
- **2_related:22, gim2024promptcache "caching the plain-text prefix"**. Prompt Cache reuses attention states of modular prompt segments, not just prefixes. Acceptable; "reusing cached attention states of the plain text" would be more precise.
- The other spot checks are accurate:
  - AGAR (arXiv 2606.12898): training-free, middle-to-late-layer attention, re-renders the attended spans enlarged, needs a first pass per query.
  - LensVLM (2605.07019): post-trained, selectively expands compressed pages on demand.
  - LLMLingua-2: small-encoder token classifier.
  - anon2026renderretain vs ref/main.pdf: regex plus windowed entropy, exact anchors, per-block routing, check-and-retry, density vs scaling-law gate; it leaves the image unchanged. Correct.
- Unused bib entries (harmless; bibtex skips them): alonso2026table, kadavath2022know, liu2024llava15, liu2024lost.

### UNVERIFIABLE (no logged evidence found; not errors)
- **3_method:L60, timing (1 s for 32K, 4 s for 128K)**: no timing log.
- **4_setup:L28, R matched to within 10% of the flagged length**: the manifests do not record this.
- **App:16, U font names (Arial / Arial Narrow)**: the sizes 6/8 px are verified from the manifests; the font is not recorded.
- **App:161, "$55"**: the decision log implies about $49 + $4 + $3 ≈ $56. Consistent.
- **Setup:L11, "<100 of ~35,000 calls dropped"**: I count 57 dropped of 30.6K calls in the RULER/NIQ/density runs, plus the LongBench and short runs on top. Consistent.

## Verified highlights (sample)
- **Abstract**:
  - pooled S−A 0.55 [0.48, 0.62] and 0.43 [0.27, 0.56]
  - 0.48 at 32K–128K
  - NIQ 0.23 → 0.48
  - X−K range −0.01 to +0.04
- **Tab. 1 means**: 5-reader A 0.08/0.22, S 0.64/0.65, U 0.12/0.21, Z 0.16/0.19, R 0.10/0.10; F1 pooled 0.46/0.34 (Holm 14 and 9 of 15); 842 vs 920 billed.
- **Controls**: S−R 0.54/0.56; B−A −0.048, CI upper bound −0.001; S−B 0.53.
- **Length study**:
  - A recall 0.12/0.08/0.07; S 0.60/0.575/0.555
  - 35/45 Holm-significant cells
  - 5.43×/6.84×/7.96× fewer tokens than text; text recall ≥ 0.99
- **Milder budgets**: 1.52× and 2.33× the vision tokens; S−A 0.38/0.20; S−U 0.26/0.04.
- **NIQ**: 12% cheaper; 4/5 significant; 1/60 flagged; −0.01 [−0.11, 0.08].
- **Anchors**:
  - 1.0 anchor per single-needle document, gold value always included
  - K/X 0.90–1.00; multi-key F1 0.46–0.52
  - 5.3 anchors; random pick 0.44
  - frontier 0.75/0.76/0.81 at 1017/1128/1306 vs 0.71/0.74/0.77 at 1014/1267/1345
  - X 31%/29% cheaper than K at 64K/128K; multi-key F1 0.36–0.40
- **LongBench**: per-cell means; S−A +0.02 [−0.02, 0.06]; X−A +0.02 [−0.03, 0.07]; X−T 9/10 cells, 0.15–0.33; Qwen HotpotQA −0.058.
- **Detector ablation**: 0.77/0.78, 0.33/0.32/0.82; fallback to uniform in 24/25 documents.
- **Routing**: τ median 0.3 (range 0.1–0.5); 0.97@0.69× vs 0.93@0.70×; Claude 0.98@0.61×.
- **Appendix**:
  - 10/180 images +1.2%
  - Z scale 0.52–0.64
  - phase-diagram peaks and 7.8–21.1 chars/vtok
  - MiniMax abstention ≤ 5.6%, silent errors 0.40 → 0.31
  - pilot detector 85/112 flags, 62% years; −0.05 (3/12) / −0.005 (1/12) / +0.000
  - local shrinking 84% retention, +0.003
  - line spacing 0.00 [−0.09, 0.09]
  - 14/60 artifacts
  - linear fit 0.208/0.737/1.1%
- **Teaser**: Claude's answer is a well-formed UUID with 4 wrong characters; allocation draws it at s_hi 12 / s_lo 6 on a 31.9K-character document.
