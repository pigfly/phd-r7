# Integrity check: "why allocation works" text (uncommitted diff, 2026-11-10)

Verdict: FAIL (6 blocking items; all fixable by rewording, no new experiments needed)

## Numbers verified (PASS)
Source: analysis_why.json, recomputed from preds with why_analysis.py logic.
- Anatomy, uniform (A): 119/375 empty = 32% ("a third"); hyphens 0.993, hex 0.510; exact 0.232; 1-7 wrong 0.177; >=8 wrong 0.591; median 27 (among >=8); 32x15/16 = 30 expected from guessing. Allocation (S): hex 0.910, hyphens 0.978, exact 0.581, >=8 wrong 0.088, empty 50/373 = 13%.
- Appendix confusion counts 8>0 43, 0>8 31, 8>b 24, 6>d 23, 8>9 22, 3>1 22 match the json (but see B1 for what they are computed over).
- esz exact|found, 5-10 px: E 0.54-0.78, W 0.64-0.71, H 0.12-0.42. Char|found: E/W 0.90-0.97 (all sizes), H 0.81-0.91 (5-10 px). E at 4 px 0.951 (n=11 found). H found at 4 px 0.02. H found n per cell 24-98. H found > E found at every size >=5 px.
- Geometry: 14/4.0 = 3.5 chars per patch; 28/4 = 7 chars x floor(28/9) = 3 lines per token; 14/7 = 2 chars at 12 px.
- Retained numbers match HEAD text: 0.43-0.55, 0.48, 0.23 to 0.48, 0.33 vs 0.32, 0.82, 0.90-1.00, F1 0.46-0.52, 5.3 / 0.44, 0.75-0.81, 0.02-0.05 (X-K = +0.04/+0.02/+0.05), 29-31%, 0.36 vs 0.44, +0.02 [-0.02,0.06] / +0.02 [-0.03,0.07], 0.15-0.33 in 9/10. Pooled rows that remain are unchanged.
- LaTeX: full.log has no undefined references; no "??" in main.pdf or supplementary.pdf; every \cref target has a label; References start on page 8 and the conclusion ends on page 8.

## Blocking
B1. sec/5_results.tex:54. The text says "Among partial misreads ... (8/0, 8/b, 6/d, 3/1)". This is wrong. top_confusions is counted over all right-length answers, so it includes the fabrications. Restricted to partial misreads (1-7 wrong; 89 errors), the top confusions are 8>0 (24), 1>i (6), 8>d (4), 0>8 (4), 6>d (3). 8>b, 8>9 and 3>1 come almost entirely from fabricated answers (8>b 23 of 24, 3>1 21 of 22), so they say nothing about glyph shape.
 Fix: "In partial misreads the dominant confusion is 8->0 (24 of 89 wrong characters), followed by 1->i and 8->d." In X_appendix.tex:139, either restrict the counts to partial misreads or say "over all right-length answers, including fabrications", and drop "which a patch cannot separate" for the fabrication-driven pairs.

B2. sec/5_results.tex:127. The text cites the S LongBench F1 "+0.02 [-0.02, 0.06] ... (\cref{tab:pooled})", but the diff deleted the S-A LongBench row from tab/pooled.tex. Only X-A remains.
 Fix: restore the row, or cite tab:app_pooled for the S value.

B3. sec/5_results.tex:65. "At 10 px the uniform image is already legible enough" contradicts the paper's own esz data. At 10 px, uniform hex is found 98% of the time but copied exactly only 22% (exact|found 0.22). On RULER at 10 px, S-A is still +0.20; it is only S-U (font search) that is ~0. Fix: "At 10 px, a font/size search on the uniform image recovers most of the gain (S-U +0.04)."

B4. esz has a reader-composition (Simpson) confound that the text does not acknowledge. Affected text: 5_results.tex:56-61, contribution 1 in 1_intro, the fig:why caption, and tab:app_esz ("five readers").
 - Found counts, pooled over sizes. Gemini: E 87, W 105, H 102. GPT: E 37, W 38, H 48. Llama: E 24, W 35, H 38. MiniMax: E 1, W 1, H 43. Qwen: E 5, W 13, H 48.
 - So the pooled E/W "found" set is mostly Gemini, while H includes MiniMax and Qwen, which copy essentially no hex exactly. MiniMax and Qwen answer with the key for E/W (e.g. "jolly-bridge").
 - Within-reader exact|found still shows the gap for the three readers that find E/W. E / W / H: Gemini 0.78 / 0.80 / 0.60, GPT 0.57 / 0.53 / 0.08, Llama 0.46 / 0.29 / 0.00. The pooled 54-78% vs 12-42% overstates its size.
 Fix: report the within-reader comparison for the three readers, or add a sentence such as "MiniMax and Qwen3-VL rarely return English or word targets, so the comparison rests on Gemini, GPT and Llama; within each of them hex is copied exactly less often." In the contribution, say "three readers".

B5. sec/1_intro.tex:29-30 and 5_results.tex:48-52 ("Wrong answers are fabricated, not misread"). The fabrication pattern comes from two readers.
 - Of the 107 uniform right-length answers with >=8 wrong, 95 are from Llama (40/40 fabricated) and MiniMax (55/55).
 - Gemini fabricates in 1% of its answers (hex accuracy 0.96, exact 0.59): its errors are misreads.
 - The pooled "format read, content not" claim (hyphens 99% vs hex 51%) is driven by the same two readers.
 - The A->S hex gain does hold for every reader individually: 0.96->1.00, 0.68->0.93, 0.16->0.85, 0.15->0.82, 0.58->0.93.
 Fix: "pooled over readers ...; fabrication dominates for Llama and MiniMax, while Gemini mostly misreads single characters". Report the per-reader A->S hex gain as the robust result.

B6. sec/1_intro.tex:31. "fills them in from the prior instead of abstaining, which is why the errors are silent" conflicts with the data: a third of uniform answers are empty, i.e. abstentions. Fix: "often fills them in ... rather than abstaining, so many errors are silent".

## Non-blocking (calibration)
- 3_method.tex, Eq. reading: present it as an idealized/schematic model ("We model reading schematically as ..."). Reword "the failure mode Eq. predicts" (5_results:52) as "consistent with". VLMs do not factor this way, and nothing in the paper tests the decomposition.
- 5_results.tex:63-67: change "This account also explains" to "is consistent with". "Boxing does not help because legibility, not search" is interpretive; esz shows hex found-rates rising with size (24% at 5 px to 98% at 10 px), so finding is also size-limited. "Shrinking prose costs little because the prior reconstructs it" is untested: the LongBench null result does not identify the mechanism. Write "plausibly because".
- 5_results.tex:61: "because English values were sometimes not recognized as codes" is speculation. Say "readers often returned the key instead".
- esz design confounds to state in app:why:
  (a) Hex differs from E/W in alphabet as well as predictability. Digits and confusable glyphs (8/0/b/6) mean glyph confusability is a confound alongside entropy.
  (b) The E "phrase" keeps only all-lowercase words, then takes consecutive ones from that filtered list. It is therefore not a contiguous span: capitalized words, numbers and punctuated tokens are removed. The code also limits W to 3-8-letter words.
  (c) "Exact" means the gold is a case-insensitive substring of the answer, so over-long answers count. One Qwen E answer counts as exact but not as found.
  (d) "Char. acc." is a SequenceMatcher ratio, bounded below by the >=0.5 selection. Call it "similarity". The 0.5 threshold itself is safe: random hex pairs score 0.24 on average and never reach 0.5.
  (e) The 4 px E figure (95%) rests on 11 found answers. Give n.
- 3_method.tex:52: patch/token geometry is the Qwen2-VL accounting convention, not each reader's actual patching. Add "in the accounting of Eq. (cost)".

## Round 2

Verdict: **PASS**

B1 (top_confusions over all vs. partial misreads) — FIXED. sec/5_results.tex:438-441 now reports "the most frequent confusion is 8→0 (24 of 89 wrong characters)" for partial misreads, matching `anatomy.A.top_confusions_partial` (8>0: 24, n_wrong_partial: 89). sec/X_appendix.tex:137-139 separates "over all right-length uniform answers, fabrications included" (8→0, 0→8, 8→b, 6→d, 8→9, 3→1, matching `top_confusions`) from "among partial misreads alone (89 wrong characters), 8→0 dominates (24), followed by 1→i (6)" (matching `top_confusions_partial`).

B2 (deleted S-A LongBench row) — FIXED. sec/5_results.tex:543-546 now cites "(Tabs. 2 and 7)" i.e. `\cref{tab:pooled,tab:app_pooled2}`; tab/app_pooled2.tex:61 has "LongBench QA (F1) & S−A & F1 & +0.02 & [-0.01,+0.04] & [-0.02,+0.06]", matching the number cited in the text and the task's check value exactly.

B3 ("uniform already legible enough" at 10px) — FIXED. sec/5_results.tex:463-465: "font/size search recovers most of the gain (S−U +0.04), because larger uniform glyphs already supply more evidence" — matches tab/pooled.tex row S−U,10px = +0.04 [-0.04,+0.12].

B4 (esz reader-composition confound) — FIXED. New `esz.per_reader_found_5to10` in analysis_why.json is used directly: sec/5_results.tex:450-459 and tab/app_esz_rd.tex restrict the transcription comparison to "the three readers that found enough targets of every type" (Gemini/GPT/Llama), reporting hex 0.61/0.08/0.00 vs English 0.82/0.57/0.46 vs random words 0.89/0.53/0.29 — all match json (Gemini H=0.61/E=0.816≈0.82/W=0.89; GPT H=0.083≈0.08/E=0.568≈0.57/W=0.526≈0.53; Llama H=0.0/E=0.458≈0.46/W=0.286≈0.29). tab/app_esz.tex caption now says "pooled over five readers, whose mix differs across types"; tab/app_esz_rd.tex caption explains MiniMax/Qwen exclusion. 1_intro.tex contribution bullet now says "each of the three readers we can compare" (not "five readers").

B5 (fabrication driven by two readers) — FIXED. 1_intro.tex: "for four of five readers most wrong answers of the right length are not misreadings." sec/5_results.tex:432-436 and tab/app_anatomy_rd.tex give the per-reader breakdown; fabricated rates under A match json per_reader exactly (Gemini 0.01, GPT 0.62/0.63, Qwen 0.86, Llama 1.00, MiniMax 1.00), and under S range 0.00-0.19 (task's "fabrication 0→19%" check confirmed: MiniMax 0.19 is the max). Hex-accuracy range A→S "0.15-0.96 to 0.82-1.00" is retained in sec/5_results.tex:... and matches per_reader hex_acc min/max (A: 0.146→0.15 MiniMax, 0.963→0.96 Gemini; S: 0.823→0.82 MiniMax, 1.0 Gemini).

B6 (abstention vs. silent-fill contradiction) — FIXED. 1_intro.tex: "the reader often fills them in from the prior rather than abstaining, so many errors are silent" — matches suggested fix, no longer claims causality contradicted by the ~32% empty-answer rate.

Calibration items — all addressed:
- Eq. framed as "a schematic model" (3_method.tex:principle); "Cref{sec:principle} predicts... are consistent with this" (hedged, not a proof claim).
- "This account also explains" → "The account is also consistent with"; boxing claim hedged to "suggests... not search alone"; "Shrinking prose costs little" → "plausibly because" (verbatim match to suggested fix).
- esz confounds (a)-(e) all now stated in app:why: glyph confusability alongside entropy; E-phrase construction (lowercase-only, not contiguous); exact = case-insensitive containment; similarity-ratio floor with random-hex-pairs baseline "average 0.24 and never reach 0.5" (matches task's calibration check); 4px n given as "11-14 found answers" (matches `E|4.n_located=11`, `W|4.n_located=14`); non-monotonic hex pattern across sizes with n=24-98 flagged as uninterpreted.
- 3_method.tex:52 geometry now framed as "under the patch convention of Eq. (vtok)" (accounting convention, not literal).
- Remaining minor non-blocking item: X_appendix.tex app:why still says MiniMax/Qwen "did not recognize [English/word targets] as codes and answered with the key instead" — the "did not recognize as codes" clause is speculative (same substance as the original flagged sentence, only reworded), but this is non-blocking per the original report and does not affect any numeric claim.

Numbers re-verified directly against thoughts/exp/real/analysis_why.json: per-reader hex accuracy 0.15-0.96 → 0.82-1.00 ✓; fabrication 0-19% under S (MiniMax 0.19) ✓; 8→0 24 of 89 ✓; per-reader esz exact|found 0.61/0.08/0.00 vs 0.82/0.57/0.46 (Gemini/GPT/Llama) and random words 0.89/0.53/0.29 ✓; 11-14 found answers at 4px (E=11, W=14) ✓; similarity 0.24 for random hex pairs ✓.

LaTeX/build checks: `grep -ni undefined full.log` → no matches; no "??" in main.pdf or supplementary.pdf text; `pdfinfo` + `pdftotext` confirm "6. Limitations and Conclusion" and "Conclusion." on page 8, "References" starting page 9 of main.pdf. fig/why.pdf, full.log, and main.pdf all postdate the current analysis_why.json and make_figures.py (timestamps 09:38-09:40), so the compiled PDFs reflect the current sources.

No remaining blocking items.
