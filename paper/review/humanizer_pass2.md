# Humanizer pass 2 (CVPR register)

Scope: sec/0_abstract, 1_intro, 2_related, 3_method, 4_setup, 5_results, 6_conclusion, X_appendix, fig/method.tex caption, teaser caption in main.tex, two table captions (data/make_tables.py, data/make_appendix_tables.py). Section structure and paragraph count unchanged.

## Patterns removed, by type

- **Overlong / clause-stacked sentences (main fix, ~60 splits).** Sentences over ~30 words split at semicolons or clause boundaries. Roughly 65 such sentences in the main body before; about 20 remain, mostly definitional lists (detector patterns) or number lists.
  - Abstract: "...at the two densest budgets (95% CIs ...) and by 0.48 at 32K--128K characters, while using up to 27% fewer billed tokens." -> two sentences; the 27% saving is now attached to the 32K--128K result (its actual source, 13--27%).
  - Results 5.5: "X thus lies on or above K's frontier ..., although the pooled confidence intervals all include zero ..." -> two sentences, caveat kept in full.
  - Related work: the DeepSeek-OCR/Glyph/... and FastV/SparseVLM/... citation chains are broken into 2--3 sentences each.
- **Connective overuse.** Fewer stacked "however"/"therefore" (e.g., abstract's final "however" removed; intro "Relative to plain text, however," -> plain sentence; related work's second consecutive "We therefore report" -> "We report").
- **Formulaic openers / filler.** "A growing line of work reduces" -> "Recent work cuts"; "Our observation is that the renderer already holds" -> "The renderer already holds"; "The cost of uniform resolution is not uniform." (wordplay) -> "Uniform resolution hurts some strings far more than others."; "a meaningful and controllable cost" -> "a controllable cost"; "note the log scale" -> "log scale"; "first start to fail" -> "begin to fail".
- **Copula avoidance.** Appendix "which serves as a replication of" -> "which gives a replication of".
- **Over-claiming verb.** Intro "We confirm the problem at long-context scale" -> "We find the same problem at long-context scale".
- **Awkward construction.** Conclusion "we do not measure ... the fact that text inside images bypasses ..." -> "the effect of text inside images bypassing ..."; related "is an open question that we do not test" -> "we do not test whether ...".
- **Captions.** fig/method: semicolon chain split into sentences, "Our contribution is Allocate." folded into the Allocate sentence. Teaser: final semicolon split. Fig. examples and Fig. density captions: semicolon chains split. Table captions: `tab:app_pooled` ("On natural strings, recall and F1 coincide; on LongBench, only F1 is defined.") and `tab:detector` (active voice for the detector sentence).
- **Em-dashes.** None in prose before or after (the only `---` are TikZ comment rules in fig/method.tex).
- **Arm names.** A, U, Z, R, B, S, K, X, T unchanged; no synonym cycling introduced.

## Claims touched

No claim strength was changed. All hedges kept ("plausibly", "perhaps", "consistent with", "suggests", "indicative", "can mislead"), as were all conditions ("for flagged targets", "where prose can shrink", "five non-Claude readers", "in our tests").
- Abstract 27% sentence re-attached to the 32K--128K result (see above). This reflects where the number comes from; it is not a stronger claim.
- "plausibly because both spread legibility" -> "Both plausibly fall short because they spread legibility" (same hedge).
- Intro "under the constraint that the image costs no more" -> "subject to the image costing no more" (constraint wording kept).

Flagged for the author, not changed:
- Intro contribution 4 and Limitations say anchors "mislead readers when the target is not flagged". The evidence (X-K = -0.08, CI [-0.17, 0.01]) includes zero, and Results 5.5 says "can mislead". Consider using "can mislead" everywhere.
- Memory note "Paper: no R-or-R citation" vs. the `anon2026renderretain` cite that is still present throughout. Not touched, since cite keys are frozen in this pass.

## Checks

- `python3 data/humanizer_guard.py check` -> `OK: no number, citation, or label changed`.
- `diff -r /tmp/tab_before_humanize tab`: only the caption lines of `app_pooled.tex` and `detector.tex` differ; all table bodies and numbers are identical.
- Teaser caption (main.tex, not covered by the guard): checked by hand, numbers unchanged.
- Build (pdflatex/bibtex/pdflatex x2): 0 undefined references, 0 errors. Conclusion ends on page 8 ("...on ordinary comprehension remains."), and References starts at the top of page 9. Before this pass, the Conclusion ran three lines onto page 9.
