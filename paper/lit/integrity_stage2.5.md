# Stage 2.5 Integrity Check: "Spend Pixels Where It Hurts" (CVPR 2027 draft)

Verifier: independent subagent, 2026-11-04. Scope as requested: (1) numbers, (2) claims vs evidence, (3) citations, (4) reproducibility statements vs code. The "AI research failure mode" checklist was not run (user override).
Sources: `thoughts/exp/real/analysis_*.json|txt`, manifests/gt/pred files in `thoughts/exp/real/<run>/`, the scripts `make_items.py`, `ruler_niah.py`, `run_openrouter.py`, `run_minimax.py`, `run_text.py`, `analyze_ruler.py`, `analyze_longbench.py`, `longbench_qa.py`, `niq.py`, `route_density.py`, `real_density.py`, the decision log / pilot log, and arXiv/ACL primary sources for citations. All means were recomputed from raw per-cell values; nothing was copied from `numbers.json`. The compiled `main.pdf` matches the `.tex` sources (checked by spot-grep).

## Summary counts

| Check | Items | Verdicts |
|---|---|---|
| 1. Numbers (grouped rows in Table A) | 118 rows + 1 item outside the table (M8) | MATCH 99 · ROUNDING-OK 6 · MISMATCH 9 (+M8 = 10) · UNVERIFIABLE 3 |
| 2. Claims vs evidence | 16 flagged | 3 contradicted by data (C1-C3) · 13 overstated/imprecise (C4-C16) |
| 3. Citations (46 cited keys, 4 bib entries uncited) | 46 | ACCURATE 40 · IMPRECISE 6 · WRONG 0 · formatting notes 2 |
| 4. Reproducibility vs code | 11 flagged | 5 contradictions (R1-R5) · 6 imprecise/undisclosed (R6-R11) |

**Overall verdict: FAIL.** There are 10 numeric MISMATCHes, 3 claims the data contradict, and 5 procedure statements the code contradicts. None of them overturns a headline result. Recall gains, the 33/36 and 63/72 significance counts, the 46/54 length cells, the NIQ means, and the LongBench F1s all reproduce. Several of the problems do need text or table changes before submission. The most consequential are M1 (the characters-per-vision-token densities are wrong for every long-document experiment), R1 (the random-word ablation does not enlarge "the same total length"), M9 (the short-document prose claim is contradicted by the paper's own table), and M10 (the teaser caption contradicts the data and Section 3).

---

## Table A: numeric items

Reader subsets: "6R" = all six API readers, "5R" = six minus Claude, "5B" = the five readers that report billing (MiniMax excluded), "4B" = 5B minus Claude.

| # | Location | Paper value | Recomputed (source) | Verdict |
|---|---|---|---|---|
| 1 | Abstract, 5.2, 3.4 | S−A +0.45–0.49 at 32K–128K | 0.4496 / 0.4844 / 0.4899 (rlong, 6R×3 tasks) | MATCH |
| 2 | Abstract, 3.4, 5.2 | 15–28% fewer billed tokens | 14.7% / 23.3% / 28.2% (5B) | MATCH |
| 3 | Abstract, 1, caption Tab.1 | 63 of 72 better, 0 worse vs U/Z | S−U 17+14, S−Z 16+16 = 63; worse 0 (rbx) | MATCH |
| 4 | Abstract, 1, 5.5, 6 | NIQ recall 0.23 → 0.76 | A 0.2334, X 0.7568 (niq2, 5R) | MATCH |
| 5 | Abstract, 1, 6 | "about one fifth" / ≈0.2× text cost | X/T = 1127.7/5323.6 = 0.212 (4B) | MATCH |
| 6 | Abstract | synthetic needles in sparse docs 0.99 | X k=4 0.987, k=1 1.000 (rdens 6R) | MATCH |
| 7 | Abstract, 5.6 | no significant loss in 12 cells (X) | X−A: 0 of 12 CI<0 (lb3) | MATCH |
| 8 | Intro | 128K essay 27.1K text vs 5.0K image tokens | T 27,106 (4B); A 4,954 is 5B incl. Claude; same 4B readers A = 4,665 | **MISMATCH** (M5) |
| 9 | Intro, 5.1 | uniform recovers 9–28% (16K) | A mean 0.0939 / 0.2763 (6R) | MATCH |
| 10 | Intro | ~1 in 8 needles near-miss under uniform | silent_A 0.132 (5px), 0.119 (6px), 0.13–0.15 long | MATCH |
| 11 | Intro, App.C | "[unreadable]" used for ≤6% | MiniMax abstain 0.056 / 0.044 / 0.022 / 0.000 | MATCH |
| 12 | Intro, 5.2 | uniform recall 0.20 at 32K → 0.13 at 128K | 0.1952 → 0.1348 | MATCH |
| 13 | Intro contrib. | +0.42–0.57 at 16K–128K | 0.4209 (16K 6px) … 0.5708 (16K 5px) | MATCH |
| 14 | Intro contrib. | "more than triple" NIQ | 0.7568/0.2334 = 3.24× | MATCH |
| 15 | 3.2, App.C | preliminary detector 85–112 / "85 and 112" flagged words per MFQA / HotpotQA doc | 84.7 (lb_s6_mfqa), 111.58 (lb_s6_hotpot) gen logs | MATCH |
| 16 | App.C | 62% of them years | decision log Iter 15 (no script output) | UNVERIFIABLE (log only) |
| 17 | 3.2, App.A | detector rules (hex≥8, ≥5 digits, entropy ≥3.5 over 16 chars, ≥20 id chars) | `HAZ_STRICT`, `flagged()` in make_items.py | MATCH |
| 18 | 3.1 / App.A | 28×28 px per token; 1008 px = 36 patches; 4 px margin; 2016 px pages | make_items.py `vtokens`, `W`, `MARGIN`, `paginate` | MATCH |
| 19 | 3.3 | s_hi ≤ 12, s_lo ≥ 5 | `S_HI=12`, loop to 5 | MATCH (lower bound of s_hi differs, see R6) |
| 20 | 3.3 | ~1 s at 32K, ~4 s at 128K | re-timed: 0.68 s, 4.05 s | MATCH |
| 21 | 3.3 / Fig.1 | UUID at 12 px, prose stays at 6 px | teaser item 1: S (s_lo 6, s_hi 12) | MATCH (but contradicts teaser caption, M10) |
| 22 | 3.4 | 15–28% fewer billed tokens (long runs) | see #2 | MATCH |
| 23 | 3.5 | c(w)=\|w\|/2+3 | `anchor_tok` formula | MATCH |
| 24 | 3.5, App.A | τ median 0.3; range 0.1–0.5 | taus [0.5,0.3],[0.3,0.3],[0.1,0.1],[0.5,0.3] → median 0.3 | MATCH |
| 25 | 4 Setup | **5/6 px ≈ 21 and 14 chars per vision token** (also Tab.1 caption + header) | 16K RULER: 31.5 (5px) / 21.1 (6px); 32K–128K: 21.1–21.4 at 6px; LongBench/NIQ 20.9 at 6px. 21.1/14.0 hold only for the 1.6K short docs | **MISMATCH** (M1) |
| 26 | 4 | 32 of 14,010 calls dropped | exact for rbase + rlong(image) + rdens(image, incl. agent reader) + rdet + lb3 only; excludes rabl, niq2, all text-arm calls, lb2, lb_s6, sw, run3/run4, ruler2, which the paper also reports (≈32K calls, ≈73 drops under the same rule) | **MISMATCH** (M6) |
| 27 | 4 | N=25 (16K, 32K), N=20 (length), N=50 (LongBench) | gen logs / manifests | MATCH |
| 28 | 4 | 10,000 bootstrap resamples, 95% | `boot(n=10000)` | MATCH |
| 29 | 4 | up to three pages at 32K–128K | 128K pages {2,3} | MATCH |
| 30 | 4 | LongBench contexts ≤40K chars | max 39,750 / 39,714 | MATCH |
| 31 | Tab.1 | all 84 per-reader recall cells | rbx per-reader means | MATCH (84/84) |
| 32 | Tab.1 | Mean A 0.09 / 0.28; U 0.14 / 0.28; S 0.66 / 0.70; K 0.97 / 0.95 | 0.094/0.276; 0.136/0.281; 0.663/0.697; 0.971/0.948 | MATCH |
| 33 | Tab.1, 5.1 | Z mean 0.17 / 0.23 | 0.167 / 0.2350 (exact tie, rounded down) | ROUNDING-OK |
| 34 | Tab.1, 5.1 | R mean 0.11 / 0.09 (5R) | 0.108 / 0.092 | MATCH |
| 35 | Tab.1, 5.1 | **X mean 0.98 / 0.99 (5R)** | 0.9793 / **0.9953 → 1.00** (double rounding 0.9953→0.995→"0.99") | **MISMATCH** (M3) |
| 36 | Tab.1 billed | 779/775/768/808/779/823/857; 913/891/887/901/812/960/881 | identical (5B; R, X on 4B) | MATCH |
| 37 | 5.1 | Claude 0.57, Gemini 0.88 at 6px; others ≤11% | 0.573, 0.877; max 0.113 | MATCH |
| 38 | 5.1 | S gains 0.57 and 0.42 | 0.5708 / 0.4209 | MATCH |
| 39 | 5.1 | S>A in 33 of 36 cells | 17 + 16 | MATCH |
| 40 | 5.1 | S worse than U/Z in 0 of 72 | 0 | MATCH |
| 41 | 5.1 | S 11% cheaper than A at 6px | 812.1/913.1 → 11.1% | MATCH |
| 42 | 5.1 | Llama 0.00→0.58, MiniMax 0.00→0.57 at 5px | 0→0.577, 0→0.567 | MATCH |
| 43 | 5.1 | R significantly worse than A in 5 of 15 at 6px | 5 (3× Gemini, GPT, Qwen) | MATCH |
| 44 | 5.1 | S−R 0.53 / 0.56, 14 of 15 each | 0.531 / 0.561; 14, 14 | MATCH |
| 45 | 5.1 | K 0.97 / 0.95 | 0.971 / 0.948 | MATCH |
| 46 | 5.1 | **K "5% more tokens" than A** | 5px: 822.9/778.6 = +5.7%; 6px +5.1% | **MISMATCH** (minor, M7) |
| 47 | 5.1 | silent A/S 0.13 / 0.16 at 5px; K 0.002 | 0.132 / 0.156 / 0.0022 | MATCH |
| 48 | 5.1, caption | K on same 5R: 0.97 / 0.94 | 0.9747 / 0.9385 | MATCH |
| 49 | 5.1 | X−K +0.06, 3 of 15 sig. (6px) | 0.0567, 3 | MATCH |
| 50 | 5.1 | X 9% cheaper than K (881 vs 968) | 4B: 881.16 vs 968.18 → 9.0% | MATCH (968 does not appear in the table, which shows K over 5B = 960; say "same four readers") |
| 51 | 5.1 | X 4% cheaper than A | 4B A 920.4 → 4.3% | MATCH (table A 913 is 5B; 881/913 = 3.5%) |
| 52 | 5.1 | at 5px X costs same as K, same accuracy | 857.3 vs 859.7; X−K 0 sig | MATCH |
| 53 | 5.2 / Tab.app_length | uniform 0.20 / 0.15 / 0.13 (text) | 0.1952 / 0.1528 / 0.1348 | MATCH |
| 54 | Tab.app_length | **Mean A at 128K "0.14"** | 0.1348 → 0.13 (double rounding 0.1348→0.135→0.14); contradicts text "0.13" | **MISMATCH** (M2) |
| 55 | Tab.app_length | 36 per-reader cells | rlong per-reader means | MATCH (Gemini 32K A = 0.475 exactly, shown 0.47; see #61) |
| 56 | 5.2 | S 0.64 / 0.64 / 0.62 | 0.6438 / 0.6393 / 0.6237 | MATCH |
| 57 | 5.2 | advantage 0.45 → 0.48 → 0.49; 46/54 sig | 14 + 16 + 16 | MATCH |
| 58 | 5.2 | **5.4×, 6.6×, 7.6× fewer than plain text** | the paper divides T (4B) by S (5B, incl. Claude). Matched 4B: **5.43×, 6.84×, 7.96×** | **MISMATCH** (M4; conservative direction) |
| 59 | 5.2 | text recall ≥0.99 for every reader | reader means 0.9917–1.00 (one Llama cell 0.975) | MATCH |
| 60 | 5.2 | S range 0.47–0.97 at 128K | 0.471 / 0.967 | MATCH |
| 61 | 5.2 | Gemini S 0.91→0.70; uniform 0.48→0.21 | S 0.913→0.704; A 0.475→0.213. Text says 0.48, table says 0.47 | ROUNDING-OK (make text and table consistent) |
| 62 | 5.2 | per-reader trend statements (Claude/MiniMax up, GPT/Qwen/Llama stable) | Claude 0.86→0.97, MiniMax 0.40→0.56; GPT 0.59→0.50 | MATCH (GPT −0.09 is "roughly stable" only loosely) |
| 63 | Fig.3 caption | N=20, mean over six readers, billed avg over readers with usage | rlong | MATCH |
| 64 | 5.3 | S 0.50 / 0.33 / 0.13 at k=1/16/64 | 0.500 / 0.327 / 0.133 | MATCH |
| 65 | 5.3 | s_hi 12 → 7 px at k=256 | gen_rdens_k256: (5,7) all 25 | MATCH |
| 66 | 5.3 | K 0.39 at k=64, 1.8× uniform tokens | 0.387; 2653.8/1492.1 = 1.78 | MATCH |
| 67 | 5.3 | k=4: X 0.99, −13% vs A, −20% vs K | 0.987; 12.6%; 19.5% | MATCH |
| 68 | 5.3 | k=16: X +0.10 over K, 13% cheaper | 0.827−0.727 = 0.100; 12.6% | MATCH |
| 69 | 5.3 | from k=64 no image arm >0.39 | max 0.387 | MATCH |
| 70 | 5.3 | τ=0.3: 0.97 @0.69× vs 0.93 @0.70× | 0.967/0.687 vs 0.932/0.698 | MATCH |
| 71 | 5.3 | k≤16: X 0.93 @0.22× vs K 0.86 @0.24× | 0.933/0.216 vs 0.860/0.243 | MATCH |
| 72 | 5.3 | k≤4 routed 0.99–1.00 @0.19–0.22× | routing txt by-k | MATCH |
| 73 | 5.3 | CV routed 0.99 @0.71× | 0.988 / 0.7115 | MATCH |
| 74 | 5.3 | "half of the documents" routed to text | k ∈ {64,128,256} = 3 of 6 densities | MATCH |
| 75 | Fig.4 caption | N=25; 6R recall, 5B cost, 4 readers for (c) | rdens, route_density.py READERS | MATCH |
| 76 | Tab.app_density | 36 K/X cells | rdens per-reader | MATCH (36/36) |
| 77 | 5.4 / App.E | 60 questions, 10 from each of 6 tasks | niq2 gt Counter | MATCH |
| 78 | 5.4 / Tab.niq | 25 per-reader cells | niq2 per-reader | MATCH |
| 79 | 5.4 | S doubles 0.23→0.48, sig. for 4 of 5 | 0.2334→0.4846 (2.08×); 4 | MATCH |
| 80 | 5.4 | X 0.76, sig. for all 5 | 5 of 5 | MATCH |
| 81 | 5.4 | X 11% cheaper than K | 1127.7/1266.6 → 11.0% | MATCH |
| 82 | 5.4 | X 5% cheaper than A | 1127.7/1180.9 → 4.5% | ROUNDING-OK |
| 83 | 5.4 | text 0.97, at 4.7× X's cost | 0.970; 4.72× | MATCH |
| 84 | 5.4 | Gemini 0.90 vs 0.92 | 0.900 / 0.917 | MATCH |
| 85 | Tab.niq billed | 1181 / 1035 / 1267 / 1128 / 5324 | identical (4B) | MATCH |
| 86 | 6 Limitations | X trails text by 0.21 | 0.970 − 0.757 = 0.213 | MATCH |
| 87 | App.E | 14 of 60 artifact questions (discarded set) | decision log Iter 21 | UNVERIFIABLE (`niq_s6` not scored in any analysis file) |
| 88 | Tab.longbench | 48 per-reader cells, sig. marks | lb3 | MATCH (48/48) |
| 89 | 5.5 | Means MFQA 0.35/0.35/0.35; Hotpot 0.58/0.60/0.60 | 0.349/0.354/0.348; 0.578/0.598/0.596 | MATCH |
| 90 | 5.5 | X: 0 negative, 1 positive of 12 | MiniMax hotpot only | MATCH |
| 91 | 5.5 | S: 1 negative (Qwen hotpot −0.06) | −0.058 [−0.124, −0.006] | MATCH |
| 92 | 5.5 | K never significantly worse | min upper bound = +0.000 (Qwen hotpot, rounded) | ROUNDING-OK (borderline; report the unrounded bound) |
| 93 | 5.5, App.C | preliminary detector −0.05 F1, 3 of 12 negative | lb_s6 M−A mean −0.0476; 3 | MATCH |
| 94 | App.C | second sample −0.005, 1 of 12; final +0.000, 0 of 12 | analysis_mlocal.txt | MATCH |
| 95 | 5.5 | nothing flagged on "almost half" of HotpotQA docs | 24 of 50 (48%) with zero strict flags | MATCH |
| 96 | Tab.detector, 5.6 | 0.22/0.77/0.78/0.99/0.99; 0.32/0.33/0.82/0.32/0.99 | 0.216/0.774/0.778/0.986/0.988; 0.320/0.326/0.824/0.316/0.990 | MATCH |
| 97 | 5.6, App.F | 13 tasks ×20; essays 36; others 40; all routing columns | analysis_real_density.txt | MATCH (17 rows × 6 columns) |
| 98 | 5.6 | prose docs 95–100% → X at 0.19–0.27×; MFQA 75% at 0.43; code 0.81–0.96×; logs/manifests 0% | same | MATCH |
| 99 | Tab.app_corpora | fit 0.208 / 0.737, MAE 1.1% | 0.2083 / 0.7367 / 1.1% | MATCH |
| 100 | 5.6 | Claude +0.32, Gemini +0.39 at 21 ch/vtok | sw_s5 M−A 0.321, 0.389 | MATCH |
| 101 | 5.6 | weaker readers +0.48 to +0.78 at 11–14 | peaks 0.483 (Qwen), 0.500 (MiniMax), 0.544 (GPT), 0.778 (Llama) at 14.0/10.7 | MATCH |
| 102 | App.B Fig.6 | densities 7.8–21.1; N=30 | make_figures runs; sw N=30 | MATCH |
| 103 | 5.6, App.G | Claude agent: 0.98 recall @0.61× (τ=0.3), N=10 | 0.98 / 0.6083 | MATCH |
| 104 | Tab.app_claude | 25 cells | analysis_claude_reader.json | MATCH |
| 105 | App.G | 0.90 X vs 0.60 K at k=64; 15 agents × 10 items | same; 5 k × 10 items × 3 forms = 150 | MATCH |
| 106 | Tab.app_short | 48 cells + significance marks | run3/run4 C−A diffs | MATCH |
| 107 | App.B | ids improve significantly in all 24 cells | all lower bounds >0 | MATCH |
| 108 | App.B | "Llama up to −0.39" attributed to real manifests | −0.39 is **synthetic, 14**; manifests max −0.38 | **MISMATCH** (M9) |
| 109 | App.B | 50–100% vs 0–10% cross-item leakage | decision log Iter 10 | UNVERIFIABLE (log only) |
| 110 | App.C | word-wrap variant +0.00…+0.12, cost ≥ uniform | ruler_s5 C−A 0.00–0.12; vtok 533 vs 506 | MATCH |
| 111 | App.C | local shrinking +0.003 (0/12), 84% of RULER gain at 6px | analysis_mlocal.txt (84% is relative to M) | MATCH |
| 112 | App.C | line spacing +0.00 [−0.09, 0.09] | run4_real_merged L−C prose 0.000 | MATCH |
| 113 | App.C | prose floor: 6–8 px ids, 13–24 points less | decision log Iter 9/10 | ROUNDING-OK (log-backed, no JSON) |
| 114 | App.A | 10 of 180 images 1.2% over budget | 10/180 (all rlong_c64k_single_3), +1.2% | MATCH |
| 115 | App.A | U picks 6px Arial / 8px Arial Narrow; Z scale 0.52–0.64 | gen logs (6,6,font1), (8,8,font2); 0.524–0.641 | MATCH |
| 116 | App.H | APIs used Nov 1–3, 2026 | file mtimes / log dates | MATCH |
| 117 | App.H | about $51 | log: ≈$49 cumulative + ≈$0.5 + ≈$3 ≈ $52.5 | ROUNDING-OK (approximate; no ledger) |
| 118 | Fig.1 caption | "renders the UUID … **shrinks the surrounding prose**"; UUID with 4 wrong chars | 4 wrong chars MATCH; but the S image has s_lo = 6 = uniform (prose not shrunk) | **MISMATCH** (M10) |

(Rows 31, 76, 78, 88, 97, 104, and 106 each group many table cells. Every cell in them was checked.)

---

## Itemized problems

### Numbers (MISMATCH)

- **M1** `sec/4_setup.tex` "s0∈{5,6} px (≈21 and 14 characters per vision token)"; `tab/baselines.tex` caption and header "(uniform 5 px ≈ 21 and 6 px ≈ 14 characters per vision token)", "5 px budget (≈21 chars/vtok)". By Eq. 1, uniform rendering of the long documents gives **≈31.5 chars/vtok at 5 px and ≈21 chars/vtok at 6 px** (rbase 16K: 31.5/21.1; rlong 21.1–21.4; rdens 21.1; NIQ/LongBench 20.9). The 21.1/14.0 figures are the 1.6K-character short-document densities (sw_s5/sw_s6). Fix: "≈32 and 21". Section 5.6 then needs rewording, since it links the short-document densities "21" and "11–14" to Table 1's budgets.
- **M2** `tab/app_length.tex` Mean row, 128K, A = "0.14". The true value is 0.1348, i.e. 0.13, which is what the intro and Section 5.2 say. Cause: `extract_numbers.mean` rounds to 3 decimals and the table formatter rounds again. Fix the generator to round once.
- **M3** `tab/baselines.tex` X mean at 6 px "0.99†" and `sec/5_results.tex` "X reaches 0.98 and 0.99". The true value is 0.9953, i.e. 1.00. Same double-rounding bug.
- **M4** `sec/5_results.tex` "5.4×, 6.6×, and 7.6× fewer than the plain text". These divide the 4-reader text cost by the 5-reader S cost (Claude has no T at these lengths). On the same four readers the ratios are **5.4×, 6.8×, 8.0×**. The decision log's "7.6×" has the same mismatch.
- **M5** `sec/1_intro.tex` "27.1K billed text tokens but only 5.0K billed tokens as a uniformly rendered image". 27.1K is over 4 readers; 5.0K includes Claude. On the same readers it is 27.1K vs **4.7K**.
- **M6** `sec/4_setup.tex` "(32 of 14,010 calls in the experiments reported here)". 14,010 and 32 match exactly only the union rbase + rlong-image + rdens-image (which includes the agent reader's 100 readings) + rdet + lb3. The reported random-word ablation, X-in-Table-1, NIQ, all plain-text arms, lb2, lb_s6, the short-document sweeps, and the M-local runs are excluded. Either restate the scope or recount (≈32K calls, ≈73 drops under `failed_read`).
- **M7** `sec/5_results.tex` "recover 0.97 and 0.95 … for 5% more tokens". At 5 px it is +5.7%; write "5–6%".
- **M8** (numeric backing for C2 below) `sec/X_appendix.tex` "its rate of wrong-but-well-formed answers did not decrease". With the "[unreadable]" prompt, MiniMax's silent rate on uniform 5 px fell from 0.40 to 0.31 (run3_s5 minimax vs minimax_unr). It rose in the other three conditions (5 px C 0.31→0.33; 6 px A 0.25→0.34; 6 px C 0.02→0.06).
- **M9** `sec/X_appendix.tex` "Prose probes are unaffected on synthetic text, but on real manifests some weaker readers lose prose accuracy (Llama up to −0.39)". `tab/app_short.tex` shows Llama **synthetic, 14: −0.39†**, which is significant. The manifest maximum is −0.38. Fix: "unaffected on synthetic text except Llama at 14 chars/vtok (−0.39); on manifests the weaker readers lose up to 0.38".
- **M10** `main.tex` Fig. 1 caption "our renderer enlarges the UUID and shrinks the surrounding prose". In the plotted item (rlong_c32k_single_3, item 1) the S image has s_lo = 6 px = uniform, so prose is not shrunk. This matches `sec/3_method.tex` ("UUID is drawn at 12 px while prose stays at 6 px"), so the two statements contradict each other. Fix the caption: "enlarges the UUID within the same budget".

### Claims vs evidence

Contradicted by the data:
- **C1** `sec/5_results.tex` §5.1 "The weaker readers benefit most in absolute terms: Llama … 0.00 to 0.58 and MiniMax … 0.00 to 0.57 at 5 px." At 5 px the largest gains are Claude (+0.65) and Gemini (+0.59). Llama (+0.58) and MiniMax (+0.57) are third and fourth, and GPT is lowest (+0.48). The statement holds only at 6 px, where Llama +0.58 / GPT +0.54 / Qwen +0.53 lead and Claude gets +0.35 and Gemini +0.12. Fix: give the 6 px numbers, or drop "most".
- **C2** `sec/X_appendix.tex` "did not decrease" (see M8). The intro's "so a downstream system cannot tell such answers from correct ones" also rests on this single reader (MiniMax). Soften both and name the reader.
- **C3** Fig. 1 caption vs §3.3 (M10).

Overstated or imprecise:
- **C4** Abstract "These strings are misread into well-formed but wrong answers, and more often as contexts grow." Failures grow with length (recall 0.20→0.13), but the well-formed near-miss rate under uniform rendering does not (0.152 / 0.125 / 0.133 at 32K/64K/128K). Fix: "and fail more often as contexts grow".
- **C5** `sec/1_intro.tex` "short prose facts rendered at the same densities are recovered far more reliably (app:short)". The short documents are at 21/14 chars/vtok, while the RULER budgets are at 31.5/21 (M1), so the densities are not the same. Weak readers also miss many prose probes under uniform rendering (run3_s5 GPT 0.38, Llama 0.24, Qwen 0.19). Fix: "at comparable densities, prose probes (0.56–0.70 mean) are recovered far more often than identifiers (0.15–0.39)".
- **C6** §5.3 "At k=16, X is 0.10 more accurate than K … because the reader must still find which copied string belongs to the queried key, and enlarged strings make that lookup easier." This mechanism is untested; §3.4 itself calls it "a plausible reason". Use hedged language here too. Also only 1 of 6 readers is significant for X−K at k=16 (GPT).
- **C7** §5.6 "Reallocation helps wherever a reader is close to, but not past, its legibility limit, which is why a single budget benefits all six readers in Table 1." This is a causal reading of a correlational sweep, and it uses short-document densities that differ from Table 1's (M1). Hedge it.
- **C8** §6 Limitations "billed costs confirm the savings for the readers we tested". At 16K and 32K, Llama is billed the same for every arm (1099 tokens at 16K; billing ignores image size), and Gemini's S costs slightly more than A (5 px 1158 vs 1138; 6 px 1156 vs 1149; 32K 1172 vs 1159). The savings come from Claude, GPT, and Qwen. Fix: "for three of the five billed readers; Llama's billing is size-independent and Gemini's slightly higher at ≤32K".
- **C9** §6 Conclusion "Across six VLMs, they … more than tripl[e] their recall on natural documents". NIQ used 5 readers (no Claude), and its cost is over 4.
- **C10** §5.3, Fig. 4 caption, and intro contribution "dominates … at every operating point / threshold". The dominance is weak: at τ=0 the two policies are identical (both all-text). It is also a 4-reader mean; without routing, X costs more than K for Qwen (0.19 vs 0.16) and recalls less for Llama (0.47 vs 0.50). Fix: "matches or dominates at every threshold (mean of four readers)".
- **C11** §5.1 R "no better than uniform rendering". At 5 px, 1 of 15 R−A cells is significantly positive. Also see R1: R enlarges far more text than S does.
- **C12** §5.6 "reallocation and anchors fall back to exactly the uniform result". In 1 of 25 rdet_mv4 documents the essay contains flagged URLs, so S and X differ from A there. Write "to the uniform rendering in 24 of 25 documents".
- **C13** §3.3 "at s0=6 px, prose shrinks to 5 px". Not always: 17/20 single-needle 32K documents, 13/20 at 64K, 22/60 NIQ documents, and 32/50 HotpotQA documents keep prose at 6 px. Write "prose shrinks to 5 px when needed".
- **C14** `tab/niq.tex` caption says "∗: paired CI vs uniform above zero", but the K column has no asterisks although all 5 K−A intervals exclude zero. Mark K, or restrict the caption to S and X.
- **C15** The LongBench S results come from the same 100 documents read twice (lb2 and lb3, seeds 11/12). §5.5 reports S with 1 of 12 negative (lb3); App. C reports "+0.000 (0 of 12 negative)" for the same documents (lb2). Disclose that these are repeat reads of the same sample, since the run-to-run variation at temperature 0 is itself informative.
- **C16** `main.tex`/`fig/method.tex` Fig. 2 caption "(a 6 px uniform image in our experiments)". Table 1 also uses a 5 px budget; write "6 px in most experiments".

### Citations

All 46 cited keys exist (prior log). Characterizations were checked against arXiv/ACL primary sources (abstracts, and HTML bodies for VTCBench and ZeroSense).

| key | sentence (location) | verdict | note / fix |
|---|---|---|---|
| zhong2026focusvtc | "combines a low-resolution global view with adaptively enhanced regions", trained (Rel.) | ACCURATE | abstract: "compressed low-DPI global views with selective region enhancement"; trained with SFT + GRPO |
| xu2026seer | "learns query-dependent selective compression" (Rel.) | ACCURATE | learns to select query-relevant images and retrieve text (SFT) |
| wan2026rtprune | "adapts pruning to DeepSeek-OCR by exploiting text density" (Rel.) | ACCURATE | "dynamic pruning ratio that adapts to token similarity and textual density". Main mechanism is high-norm selection + OT merging; optional wording "partly by adapting its ratio to text density" |
| liang2026visualmerit | "accuracy collapses when linguistic priors are removed" | ACCURATE | ~90% → ~20% under semantic corruption |
| gao2026zerosense | same sentence | ACCURATE | e.g. Fox 81.3% vs 27.4% under the decoupled evaluation |
| zhao2025vtcbench | "compressed reading loses retrieval ability" (Rel.); "as context grows" (§5.2) | ACCURATE | body: "nearly all VLMs exhibit a clear degradation … as the context length increases" (Qwen3-VL-235B 97.2% → 81.3%) |
| sun2026reading | "text–pixel gap depends strongly on font and resolution" | ACCURATE | "highly sensitive to rendering choices such as font and resolution" |
| lee2026autoencoding | "can underperform simple learned compressors" | IMPRECISE | baselines are near-zero-parameter mean pooling (not learned) and a learned hierarchical encoder. Fix: "simple direct compressors such as mean pooling" |
| cheng2025glyph | "searches for a good global rendering configuration"; U as stand-in | ACCURATE | LLM-driven genetic search over rendering configurations, one configuration applied |
| wei2025deepseekocr | "decodes text from a small number of vision tokens"; Z "resolution-compression view" | ACCURATE | |
| wei2026deepseekocr2 | co-cited for "decodes text from a small number of vision tokens" | IMPRECISE | OCR 2 is about causal reordering of visual tokens (DeepEncoder V2), not token count. Cite as "and its successor's encoder" or move |
| li2025textpixels | "other work renders distant context or interleaves rendered text with images" | IMPRECISE | it renders the whole long input as one image and evaluates it (RULER, CNN/DM), reporting savings "without degrading task performance". Move it to the "renders long inputs" clause or to the evaluation sentence (where it is a counterpoint) |
| xing2025vist, wang2024visincontext | same sentence | ACCURATE | |
| rust2023pixel, gao2024screenshots, tschannen2023clippo, lee2023pix2struct | pixel LMs / unified encoders / screenshot pretraining | ACCURATE | |
| chen2024fastv, zhang2025sparsevlm, yang2025visionzip, shang2025prumerge, bolya2023tome | token reduction descriptions | ACCURATE | |
| fang2026prunesid, lv2026vprune, zhang2026trio | "balance importance and diversity or target the output objective" | ACCURATE | VPRune: visual-only diversity selection; TRIO: inference-objective guidance |
| li2025fcotvl | "text-rich images need dedicated compression" | ACCURATE | (FCoT-VL itself is trained) |
| jiang2023llmlingua, jiang2024longllmlingua, li2023selective | token-dropping prompt compressors; Selective Context information-theoretic | ACCURATE | |
| mu2023gist, ge2024icae, chevalier2023autocompressors | "map context to a few soft tokens" | ACCURATE | |
| zhang2023h2o, li2024snapkv, xiao2024streamingllm, devoto2025expected | "KV-cache methods evict entries" | ACCURATE | |
| hsieh2024ruler, bai2024longbench | task sources | ACCURATE | the HotpotQA split actually used is LongBench-E `hotpotqa_e` (R8) |
| liu2024ocrbench | "document the same weakness in natural images" | ACCURATE | |
| ma2024mmlongbenchdoc | same sentence | IMPRECISE | MMLongBench-Doc is long PDF documents, not natural images. Fix: "in natural images and long documents" |
| wang2024qwen2vl | Eq. 1, 14-px patches merged 2×2 | ACCURATE | |
| bai2025qwen25vl, bai2025qwen3vl | dynamic resolution; reader | ACCURATE | |
| chen2024internvl15, li2025llavaonevision | "bill vision tokens roughly in proportion to pixel area" | IMPRECISE | these open models allocate tokens per 448-px tile (AnyRes/dynamic tiling) and do not bill. Fix: "allocate vision tokens roughly in proportion to pixel area (directly or via tiling)" |

Bib formatting: keys follow surname+year+keyword. arXiv-only works are `@article` with `journal = {arXiv preprint …}`, proceedings are `@inproceedings`, acronyms are brace-protected, and booktitles are consistent per venue (official ordinals for ICML/ACL/COLM). Two notes:
- (F1) `liang2026visualmerit` has `Satoshi, Okamoto`. arXiv lists "Okamoto Satoshi", and the family name is almost certainly Okamoto, so the entry should be `Okamoto, Satoshi`.
- (F2) Four entries are never cited (`liu2024lost`, `alonso2026table`, `liu2024llava15`, `kadavath2022know`). This is harmless with BibTeX, but they can be pruned.

### Reproducibility statements vs code

Contradictions:
- **R1** `sec/5_results.tex` and the Tab. 1 caption: "enlarges randomly chosen ordinary words with the same total length as the flagged strings". In `ruler_niah.py` (arm R), the length is matched over distinct picked word types, then `M.ORACLE = pick` enlarges every occurrence of those types (e.g. "that", "your", "have", "very"). In a re-run with seed 0 the enlarged length was a median 4.6–5.4× the flagged length (range 1.1–20×). The manifests confirm this independently of seed: at 5 px, 11/25 single-task R images could enlarge nothing (s_hi = 5) versus 12 px for S; at 6 px R used 719 vs 540 vision tokens. Restate the procedure ("random word types whose distinct forms match the flagged length; all their occurrences are enlarged") and note that R enlarges more text at smaller sizes. The conclusion that enlarging non-hazards does not help still stands.
- **R2** `sec/4_setup.tex` "query it once per item … at temperature 0". `run_minimax.py`/`run_text.py` call MiniMax-M3 with `--temperature 0.01`. Also, `run_openrouter.py` retries up to 4 times (MiniMax 3) whenever output fails to parse or the request errors, and `RETRY=1` re-runs failed items. Fix: "temperature 0 (0.01 for MiniMax); unparseable outputs were re-queried up to three times".
- **R3** `sec/4_setup.tex` "Empty responses and safety refusals … are dropped; outputs that cannot be parsed … count as wrong". `analyze_ruler.failed_read` drops empty responses and transport errors (URLError, HTTPError, timeouts, …). A refusal that returns text without JSON is classed "zero", i.e. counted as wrong. Fix: "Empty responses and transport errors are dropped; any other unparseable output, including refusals, counts as wrong."
- **R4** `sec/X_appendix.tex` "K and X append, after the question, the line 'Exact strings copied verbatim from the text block in the image:'". This holds for RULER/NIQ. In `longbench_qa.py` the anchors are inserted right after the image placeholder, before the question, with the header "…from the text in the image:".
- **R5** `sec/X_appendix.tex` Claude agents "using only file-reading tools". Decision log Iter 20: agents were allowed Read and Write.

Imprecise or undisclosed:
- **R6** Eq. 2 says s_hi ∈ [s0, 12]. The code (`arm_c`) searches s_hi ∈ [6, 12], so at s0 = 5 there is no s_hi = 5 candidate (fallback to 5/5). The line-spacing retry in `arm_m` triggers when the best feasible pair has s_hi ≤ s_lo, not only when no pair is feasible.
- **R7** App. A "RULER prompts follow the official template". `ruler_niah.TEMPLATE` adds "Copy each one exactly, character for character." on top of the JSON instruction. Disclose it.
- **R8** §4 "LongBench … HotpotQA". The file used is `hotpotqa_e.jsonl` (LongBench-E). Non-ASCII characters are replaced by "?" for LongBench too, not only for NIQ.
- **R9** App. E "words glued across a missing space (a period, parenthesis, or comma directly followed by a letter)". `niq.GLUED` also excludes any target containing "=" and some letter–digit patterns; after "." or ")" only an uppercase letter triggers. Minor.
- **R10** §3.5 / App. A: the frontier at fixed τ and the k≤4 figures are in-sample (per-reader median of the CV τ for the by-k table). The text does not say this. Minor.
- **R11** App. B "stateless API reader" for the 0–10% leakage comparison: that reader was MiniMax through the `mmx` CLI under a subscription. Fine, but name it.

Statements the code confirms: renderer (Menlo, grayscale, 1008 px, 4 px margin, +1 px leading, 2016 px blank-row pagination); budget computed on the unsplit uniform image; detector regexes and stripping; U and Z procedures; scoring (case-insensitive containment, LongBench first-line QA-F1 with max over golds); bootstrap (10,000, seed 0); router (c(w), τ grid, λ = 0.5, parity folds); NIQ target rules; real-corpus chunking and text-token fit; 1 s / 4 s allocation time.

## Overall verdict: **FAIL**

There are 10 numeric MISMATCHes (M1–M10), 3 claims the data contradict (C1–C3), and 5 code-contradicted procedure statements (R1–R5). No citation is WRONG. All fixes are local wording or generator fixes; no headline result changes. Suggested order: M1, R1, M9/M10, C1, then fix the double-rounding in `extract_numbers.py`/`make_tables.py` and regenerate (M2, M3).
