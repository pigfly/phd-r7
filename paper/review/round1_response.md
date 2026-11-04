# Stage 4 — Response to Round-1 Review

Scope agreed by the author on 2026-11-04: P0 (RM-1 to RM-4) plus the cheap P1 items (RM-5 to RM-8). RM-10 is handled as a scoping/limitations change.
New runs: about $4 of API spend (5 fixed readers), plus no-cost rescoring of all existing logs.

| RM | Concern (source) | Change | Evidence |
|---|---|---|---|
| RM-1 | Detector, anchors and routing come from uncited prior work (DA C1) | R-or-R is cited anonymously as `anon2026renderretain` (under review; the anonymized copy goes in the supplement). Abstract, intro, related work, method, Fig. 2 caption and appendix now credit Detect, Anchor and Route to it. The contribution is narrowed to Allocate. K and X are framed as prior-work anchors on the uniform and the allocated image. | sec/0–3, fig/method.tex, refs.bib |
| RM-2 | Anchors leak the answer; recall-only scoring rewards dumping (R1 CRIT) | `rescore.py` adds precision-aware F1, exact-set scoring, the number of values returned, the gold-in-anchors rate, and random-anchor ("pick") baselines. The paper now states that on single and multi-value tasks the anchor list *is* the answer, and that on multi-key the F1 is 0.46–0.52. The anchor comparison has moved to NIQ (6.4 anchors, random pick 0.44, K 0.74, X 0.76). Table 1 gains a Mean F1 row. | analysis_rescore.json; §5.5 |
| RM-3 | No plain-text reference on LongBench (R3 CRIT) | T was run on the same lb3 samples. Table 4 now has T: X−T is significantly negative in 9/10 cells (0.15–0.33 F1). The abstract and conclusion state this gap. | lb3_s6_*/predtext_*; §5.6 |
| RM-4 | No matched-cost K vs X frontier; no K/X at long context (EIC CRIT) | NIQ re-rendered at 5/7 px. X lies on or above K's frontier by 0.02–0.04 at every cost (not significant at 6 px). Multi-key at 64K/128K: X matches K's recall at 29–31% fewer billed tokens. | niq2_s5, niq2_s7, rv2_c{64,128}k_multikey_1; §5.5 |
| RM-5 | NIQ targets selected by the detector (circular) (R1, DA, EIC) | niq3: targets are any digit-bearing token, sampled without the detector (the detector flags only 1/60). S−A = −0.01 (no harm); X−A = −0.09 (anchors mislead); all image arms score 0.36–0.45 vs 0.96 for text. | niq3_s6; Table 3, §5.4 |
| RM-6 | Operating point sits at the floor of uniform rendering (R2, DA) | 32K context at 8/10 px. S−A is +0.38 / +0.20; S−U is +0.26 / +0.04 (n.s. at 10 px). This is reported as the method's boundary. | rv2_s{8,10}_*; §5.3 |
| RM-7 | No pooled CIs, no multiplicity control, reader sets vary (R1, EIC, DA) | One fixed set of 5 readers for every mean and pooled test (Claude reported per reader only). `stats_pooled.py` gives a reader+item cluster bootstrap and Holm correction. New Table 2 holds the pooled effects. Figures use 5-reader means. | analysis_pooled.json; tab/pooled.tex |
| RM-8 | Salience vs legibility (DA M4) | Arm B: flagged strings boxed, not enlarged. B−A = −0.05 and S−B = +0.53, so the gain comes from legibility. | rv2_box_s6_*; §5.1 |
| RM-9 | Router τ chosen in-sample | Not re-run. Routing is demoted to the appendix and the frontier is labelled in-sample. | App. density |
| RM-10 | No trained compressor / pruning | Not run (needs a GPU). Limitations name both as untested; related work no longer claims pruning is "orthogonal". | sec/2, sec/6 |
| RM-11 | Deployment (caching, latency, non-ASCII, safety filters, billing) | Limitations paragraph added; Prompt Cache cited. | sec/6 |
| RM-12 | Inconsistent headline ranges | Abstract and contributions now quote the same pooled numbers. | sec/0–1 |
| RM-14 | "Same kind of strings" overreach | Sentence removed. | sec/2 |
| RM-15 | Missing references | Added after arXiv verification: AGAR (2606.12898, the closest work: attention-guided enlargement, white-box and query-dependent), LensVLM, DocOwl2, TextMonkey, LLMLingua-2, Prompt Cache. Donut, PIXAR and PixelWorld were not added for lack of space. | refs.bib |
| RM-13/16 | Exact-match, near-miss sensitivity, confusion analysis | Not done. | — |

Items declined or deferred: RM-9 (re-selecting τ on a new seed), RM-10 experiments, RM-13 and RM-16 analyses.
