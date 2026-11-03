# Stage 2.5 Integrity Re-check, Round 2

Verifier: independent subagent, 2026-11-04. Scope: (1) status of every item in `integrity_stage2.5.md`; (2) a fresh check of all text and tables changed since commit 3d7a4ec (`git diff 3d7a4ec -- paper/sec paper/main.tex paper/fig/method.tex paper/tab`); (3) page limit. The "AI research failure mode" checklist was not run (user override). No paper or data file was modified.

How it was checked:
- Means, ratios, and significant-cell counts were recomputed from `thoughts/exp/real/analysis_ruler.json` and `analysis_longbench.json`. A cell is counted as significant when its 95% CI excludes 0.
- The corrected arm R was re-derived from `ruler_niah.py` on the `rabl2_*` gt items.
- `extract_numbers.py` and `make_tables.py` were re-run in a scratch copy (/tmp). The regenerated `numbers.json` and all `paper/tab/*.tex` files are byte-identical to the committed ones.
- `main.pdf` was compiled after the last `.tex` edit (08:40), and pdftotext contains the new strings.

## Summary

| Group | Items | RESOLVED | PARTIAL | UNRESOLVED | ACCEPTED-AS-IS |
|---|---|---|---|---|---|
| M1–M10 (numbers) | 10 | 9 | 1 (M6) | 0 | 0 |
| C1–C16 (claims) | 16 | 15 | 1 (C8) | 0 | 0 |
| Citations IMPRECISE | 6 | 6 | 0 | 0 | 0 |
| F1–F2 (bib) | 2 | 1 | 0 | 0 | 1 (F2) |
| R1–R11 (code) | 11 | 11 | 0 | 0 | 0 |
| **Total** | **45** | **42** | **2** | **0** | **1** |

New problems: 2 MISMATCH (N1, N2; N1 is also the reason C8 is PARTIAL) and 3 minor notes (N3–N5).

**Overall verdict: FAIL.** M6 (a numeric item) is only partly fixed, and the changed text adds two claims that the data contradict (N1, N2). Every number specifically requested for verification reproduces (see "Requested checks"). All three remaining fixes are one-sentence edits.

---

## Table 1: previous items

| Item | Verdict | Evidence |
|---|---|---|
| M1 densities | RESOLVED | §4 and the Tab. 1 caption/header now say "≈32 and 21". Recomputed chars / A-vtok: rbase 5 px 31.44–31.52, 6 px 21.07–21.10; rlong 21.11–21.42; rdens 21.12–21.13; niq2 21.0. The short-document "21"/"14" now appear only in App. B, where they are correct. |
| M2 128K mean A | RESOLVED | Shows 0.13 (0.1348). The generator now rounds once (`extract_numbers.mean` keeps 6 decimals). |
| M3 X mean 6 px | RESOLVED | Tab. 1 and §5.1 say 1.00 (0.9953). |
| M4 T/S ratios | RESOLVED | "on the four readers with billed costs for both, 5.4×, 6.8×, 8.0×". Recomputed 4B: 6822.2/1256.6 = 5.43, 13592.5/1987.0 = 6.84, 27105.6/3404.3 = 7.96. |
| M5 27.1K vs 5.0K | RESOLVED | Now "27.1K … 4.7K (mean of the same four readers)". T 27,105.6, A 4,665.1 (4B, rlong 128K). |
| M6 dropped calls | **PARTIAL** | "73 of about 33,000 calls in all experiments reported here". On the authors' directory list (rbase, rabl, rabl2, rlong, rdens, rdet, lb2, lb3, lb_s6, niq2, ruler2, sw_s*, run3_*, run4_real, run4_real_M; pred*.json without pred_r*) I get exactly **32,780 calls and 73 drops**. The list leaves out runs the paper reports. `ruler_s5_*` is the source of App. C "Word wrapping … +0.00 to +0.12 recall" (C−A over 24 keys; the reported three tasks: 1,800 calls, 9 drops; all four tasks: 2,160 calls, 13 drops). `run4_real_L` is the App. C line-spacing result (30 calls, 0 drops). Including both gives **≈34,600 calls and 82 drops**. Fix: "82 of about 35,000", or narrow the scope ("in the main experiments"). The previous report's own ≈32K/≈73 estimate had the same omission. |
| M7 K +5% | RESOLVED | "5–6%" (5 px +5.7%, 6 px +5.1%). |
| M8 [unreadable] silent rate | RESOLVED | "fell in one of four conditions (uniform, 21 chars/vtok: 0.40 to 0.31) and rose in the other three". run3_s5 A 0.400→0.306; C 0.306→0.328; run3_s6 A 0.25→0.344; C 0.017→0.056. |
| M9 Llama −0.39 | RESOLVED | "unaffected on synthetic text except for Llama at 14 (−0.39); on real manifests … up to 0.38". Matches `tab/app_short.tex`. |
| M10 teaser caption | RESOLVED | "enlarges the UUID within the same vision-token budget (here the prose keeps its 6 px size)". Consistent with §3.3. |
| C1 "weaker readers benefit most" | RESOLVED | "At 5 px every reader gains 0.48–0.65" (0.483–0.647, 6R). The 6 px figures: Llama 0.003→0.587, GPT 0.113→0.653, Qwen 0.067→0.600, Gemini 0.877 +0.123. All match. |
| C2 "did not decrease" and intro claim | RESOLVED | The intro now names the single reader (MiniMax-M3) and softens the claim. The appendix says "did not consistently reduce". |
| C3 Fig. 1 vs §3.3 | RESOLVED | See M10. |
| C4 abstract | RESOLVED | "they fail more often as contexts grow". |
| C5 "same densities" | RESOLVED | "in short documents at comparable densities, one-word prose facts are recovered far more often than identifiers". |
| C6 k=16 mechanism | RESOLVED | Now hedged ("a plausible reason … should"), and adds "significant for one of six readers". X−K at k=16 is significant only for GPT ([0.12, 0.52]). |
| C7 inverted-U causal reading | RESOLVED | §5.6 now says "suggests". The sentence linking it to Table 1 was removed. |
| C8 billed savings | **PARTIAL** | The rewrite names the readers, but its Llama clause is wrong (see N1). The Gemini clause is correct: S vs A billed 1158 vs 1138 (16K 5 px), 1156 vs 1149 (6 px), 1172 vs 1159 (32K); cheaper from 64K on. |
| C9 conclusion "six VLMs" | RESOLVED | "Across the readers we tested". |
| C10 "dominates" | RESOLVED | "matches or dominates … (mean of four readers)" in the intro, the Fig. 4 caption, and §5.3. |
| C11 R "no better" | RESOLVED | With the corrected R: 0 of 15 R−A cells significant at 5 px (mean +0.016), 5 of 15 significantly negative at 6 px. The text states both. |
| C12 "exactly the uniform result" | RESOLVED | "in 24 of 25 documents". In rdet_mv4, S and X differ from A only for one item (URLs flagged; 540 vs 756 vtok). |
| C13 "prose shrinks to 5 px" | RESOLVED | "when needed and otherwise stays at 6 px". |
| C14 NIQ K asterisks | RESOLVED | K now carries ∗ for all 5 readers. All 5 K−A CIs are >0 (lowest Gemini [0.033, 0.267]). |
| C15 repeat read of LongBench | RESOLVED | §5.5: "A repeat read of the same documents … gave S no negative cell". lb2 and lb3 have identical documents (50/50 each). See N4 for a residual. |
| C16 Fig. 2 "6 px" | RESOLVED | "in most of our experiments". |
| cit lee2026autoencoding | RESOLVED | "simple alternatives such as mean pooling". |
| cit wei2026deepseekocr2 | RESOLVED | "its successor reorders visual tokens causally". |
| cit li2025textpixels | RESOLVED | Moved to its own clause: "rendering a whole input as one image can roughly halve its token cost". This matches the paper (arXiv title "… It Takes Half"; `lit/verification.md`). |
| cit ma2024mmlongbenchdoc | RESOLVED | "in natural images and long PDF documents". |
| cit chen2024internvl15 | RESOLVED | "allocate vision tokens … directly or through tiling". |
| cit li2025llavaonevision | RESOLVED | Same sentence. |
| F1 Okamoto | RESOLVED | `refs.bib:66` now reads "Okamoto, Satoshi". |
| F2 uncited bib entries | ACCEPTED-AS-IS | 4 entries are still uncited. This is harmless. |
| R1 random-word length | RESOLVED | Code now matches the summed length of all enlarged occurrences, capped at 1.1× the target. Re-derived on all 150 rabl2 items: enlarged/flagged length is 0.964–1.094 (median 1.036–1.056 per run). The rabl2 gt texts are identical to rbase. R vtok stays within budget (5 px 505–507 vs A 505–507; 6 px 580–588 vs A 756). `merge_rbx.py` keeps only arm X from rabl and arm R from rabl2 (25 R rows per run). The text now says "every occurrence … matched to within 10%". |
| R2 temperature and retries | RESOLVED | "temperature 0 (0.01 for MiniMax); … re-sent up to three times". OpenRouter makes 4 tries, MiniMax 3. Minor residual: the `RETRY=1` re-run passes are not mentioned. |
| R3 drop rule | RESOLVED | "Empty responses and transport errors … dropped; any other unparseable output, including refusals …, counts as wrong". Matches `failed_read`. |
| R4 LongBench anchor placement | RESOLVED | App. A now describes both placements and both headers. |
| R5 agent tools | RESOLVED | "a file-reading tool and a tool to write their answer file". |
| R6 s_hi range and retry trigger | RESOLVED | "If no pair with s_hi > s_lo satisfies … (in the implementation, s_hi is searched over [6,12])". |
| R7 template addition | RESOLVED | "add 'Copy each one exactly, character for character.'" |
| R8 LongBench-E and ASCII | RESOLVED | §4 now names LongBench-E and the "?" replacement. |
| R9 NIQ glue rules | RESOLVED | The App. E rule list now matches `niq.GLUED` and the "=" exclusion. |
| R10 in-sample frontier | RESOLVED | App. A: "both are therefore in-sample, unlike the cross-validated aggregate". |
| R11 stateless reader | RESOLVED | "MiniMax-M3 queried statelessly". |

Minor notes from the previous Table A that needed no fix:

| Row | Status |
|---|---|
| #50/#51 (968 and "4% cheaper" on 4 readers, not in the table) | Unchanged, still correct. ACCEPTED-AS-IS. |
| #61 (text "0.48" vs table "0.47" for Gemini 32K A = 0.475) | Still inconsistent. ACCEPTED-AS-IS as ROUNDING-OK, but trivially fixable. |
| #92 (K "never significantly worse") | Qwen HotpotQA K−A has only 2 nonzero item differences, both negative. Its upper CI bound is exactly 0.000 under 20 different bootstrap seeds, so the CI includes 0. Correct as stated. |
| #16, #87, #109 (log-only) | ACCEPTED-AS-IS (UNVERIFIABLE). |

---

## New problems (changed text)

- **N1 (MISMATCH, claim vs data)** `sec/6_conclusion.tex` Limitations: "Llama is billed independently of image size".
  - This holds only for the single-page 16K images, where every arm costs ≈1,098–1,101 tokens (A, S, U, Z, R; K and X ≈1,127–1,138).
  - At 32K and beyond, Llama's bill tracks the image: S vs A is 1,657 vs 1,969 (32K mean), 2,530 vs 2,887 (64K), 4,291 vs 5,552 (128K), 1,279 vs 1,537 (NIQ), and 1,536 vs 1,971 (rdens k=4). Source: `analysis_ruler.json` keys rbx_*, rlong_*, rdens_*, niq2 for llama-4-maverick.
  - The previous report's C8 note ("At 16K and 32K, Llama is billed the same") was itself wrong for 32K. The authors carried its wording over.
  - Suggested fix: "whereas Llama's billing does not change between our 16K images (≈1,100 tokens) and Gemini bills slightly more for our images at up to 32K characters".
  - Also minor: Qwen at 16K 5 px bills S 460 vs A 443, so "confirm the savings for … Qwen" does not hold in that single cell.
- **N2 (MISMATCH, claim contradicted by the paper's own table)** `sec/5_results.tex` §5.2: "S declines with length only for Gemini (0.91 to 0.70)".
  - `tab/app_length.tex` and rlong show S also falling for GPT (0.592 → 0.554 → 0.500), Qwen (0.600 → 0.554 → 0.537), and Llama (0.504 → 0.537 → 0.471).
  - Only Claude (0.86 → 0.97) and MiniMax (0.40 → 0.56) rise.
  - Suggested fix: "S declines markedly only for Gemini (0.91 to 0.70); GPT and Qwen lose 0.09 and 0.06, while Claude and MiniMax improve".
- **N3 (minor)** §5.1 says R's "sizes and vision-token cost are therefore close to those of S".
  - Billed tokens agree (4 readers: R 814 vs S 818 at 5 px; 844 vs 842 at 6 px).
  - At 5 px, however, R's enlarged words are often smaller than S's (s_hi = 12 in 28 of 75 R images vs 66 of 75 S images).
  - At 6 px, R uses slightly more vision tokens (580–588 vs 540–576).
  - "Similar" would be safer. No number is wrong.
- **N4 (minor)** §5.5 says the preliminary detector "cost 0.05 F1 … on another sample". That sample (lb_s6) shares 26/50 MultiFieldQA and 21/50 HotpotQA documents with the Table 3 sample. App. C's "second sample" (lb2) is the same documents as Table 3 (lb3), but App. C does not say so. Write "a partly overlapping sample" and name lb2 as the Table 3 documents.
- **N5 (minor)** = M6 residual (call count scope), listed above.

## Requested checks (all verified, rbx_* without Claude)

| Claim | Recomputed | Verdict |
|---|---|---|
| R mean 0.10 at both budgets | 0.1007 / 0.0953 (5R) | MATCH |
| Tab. 1 R cells | Gemini 0.48 / 0.46, GPT 0.02 / 0.02, others 0.00 | MATCH |
| Tab. 1 R billed 814† / 844† | 814.4 / 844.0 (4B) | MATCH |
| S−R +0.54 / +0.56, 14/15 significant each | 0.538 / 0.557; 14 and 14 (non-significant: Llama single at 5 px, MiniMax single at 6 px) | MATCH |
| R−A: no significant cell at 5 px; 5/15 worse at 6 px | 0 / 0 at 5 px; 5 negative at 6 px (Gemini ×3, GPT multivalue, Qwen multivalue), 0 positive | MATCH |
| X 0.98 / 1.00 vs K 0.97 / 0.94 (5R) | X 0.979 / 0.995; K 0.975 / 0.939 | MATCH |
| ≈32 and 21 chars per vision token | 31.5 / 21.1 (16K); 21.1–21.4 (32K–128K, rdens, NIQ) | MATCH |
| 73 of about 33,000 calls | 73 / 32,780 on the authors' list; ≈82 / ≈34,600 including ruler_s5 and run4_real_L | PARTIAL (M6) |
| 5.4×, 6.8×, 8.0× | 5.43, 6.84, 7.96 | MATCH |
| 27.1K vs 4.7K | 27,106 vs 4,665 | MATCH |
| 6 px per-reader gains | Llama 0.00→0.59, GPT 0.11→0.65, Qwen 0.07→0.60, Gemini 0.88 +0.12 | MATCH |
| 5 px "every reader gains 0.48–0.65" | 0.483–0.647 | MATCH |
| Gemini 0.91 to 0.70 (uniform 0.48 to 0.21) | 0.913→0.704; 0.475→0.213 | MATCH (table rounds 0.475 to 0.47) |
| 24 of 25 documents | 24 of 25 (rdet_mv4) | MATCH |
| MiniMax [unreadable] 0.40→0.31 | 0.400→0.306 | MATCH |

## Page limit

`main.pdf` has 15 pages. The main body (abstract through the Conclusion) ends on **page 8**, whose last line is "… at about one fifth of the plain-text cost." "References" begins at the top of page 9. The LLM statement and the appendix follow the references. **PASS.**

## Overall verdict: **FAIL**

Of the 45 previous items: 42 RESOLVED, 2 PARTIAL (M6, C8), 1 ACCEPTED-AS-IS (F2), 0 UNRESOLVED. There are 2 new MISMATCHes (N1 Llama billing; N2 "declines only for Gemini") and 3 minor notes. The rerun random-word ablation, the regenerated tables, and every number specifically requested reproduce. Three local edits would make the paper pass: N1, N2, and the M6 call count or its scope wording.
