# Integrity re-verification, Stage 2.5, round 3 (narrow)

Scope: open items from round 2 (M6, N1/C8, N2), plus every changed sentence in `git diff HEAD -- paper/sec` and the page limit. Data: `thoughts/exp/real/*`, `paper/data/numbers.json`, `paper/main.pdf` (built Nov 4 08:52, after the last .tex edits).

## Verdicts

| Item | Verdict |
|---|---|
| M6 dropped calls | RESOLVED |
| N1 / C8 billed-savings limitation | PARTIAL (one exception left out) |
| N2 S vs length per reader | RESOLVED |
| Other changed sentences | MATCH |
| Page limit | PASS |

**Overall: FAIL (minor).** Only N1 is still open, and a one-phrase edit closes it.

## 1. M6: "fewer than 100 of roughly 35,000 calls ... about 0.25%"

Count: `analyze_ruler.failed_read(p) == 'drop'` over `pred*.json`, excluding `pred_r*`.

| Scope | Calls | Drops | Rate |
|---|---|---|---|
| Round-2 list (no ruler_s*), with run4_real_L | 32,810 | 73 | 0.22% |
| + ruler_s5 three reported tasks | 34,610 | 82 | 0.24% |
| + ruler_s5 all four tasks | 34,970 | 86 | 0.25% |
| + ruler_s6 (all four) | 37,130 | 96 | 0.26% |
| + niq_s6 (untracked, not cited) | 38,390 | 96 | 0.25% |

App. C's word-wrapping sentence refers only to the 5 px budget, so ruler_s5 is the appropriate scope. That gives 34,610 to 34,970 calls and 82 to 86 drops. Under every scope above the count is below 100, the rate is 0.22 to 0.26%, and the total is 33K to 38K calls. "Roughly 35,000" and "about 0.25%" are fair. RESOLVED.

## 2. N1/C8: "billed savings hold for most readers, but not for Gemini up to 32K characters or for Llama at 16K, whose billing ignores image size"

Billed prompt tokens, A vs S:

- **16K** (table1_baselines_ruler16k)
  - Claude: 5 px 635 vs 623; 6 px 884 vs 692 (saves).
  - GPT: 578 vs 557; 808 vs 604 (saves).
  - Gemini: 1138 vs 1158; 1149 vs 1156 (no saving, correct).
  - Llama: 1099 = 1099 at both budgets (correct).
  - **Qwen at 5 px: 443.4 vs 460.2. S costs 3.8% more, so this is an exception the sentence does not name.** Qwen at 6 px: 625 vs 510 (saves).
- **32K/64K/128K** (length_scaling)
  - Gemini: 1159 vs 1172 at 32K (no saving); 2254 vs 1383 and 3312 vs 2241 at 64K/128K (saves). Correct.
  - Llama: 1969 vs 1657, 2887 vs 2530, 5552 vs 4291 (saves). So "Llama at 16K" only is correct.
  - Claude, GPT, Qwen save at all three lengths.
- **Density sweep, 32K, per reader** (from rdens usage): Gemini S ≥ A at every k (1161 vs 1164 to 1185). Correct.
  - Minor: Llama S = A at k=64 and k=256 (1971).
- **NIQ** (about 24K characters): S < A for every reader with billing.
  - Gemini 1143 vs 1126 (−1.4%). This slightly contradicts "not for Gemini up to 32K", though the difference is negligible.
  - GPT 1130 vs 946; Llama 1537 vs 1279; Qwen 914 vs 791.

Verdict: PARTIAL. The Gemini and Llama clauses are correct, but Qwen at 16K and 5 px is a further exception. Suggested fix: "... but not for Gemini up to 32K characters, for Qwen at 16K and 5 px, or for Llama at 16K, whose billing ignores image size." An alternative is to scope the claim to the 6 px budget and lengths of 32K and above.

## 3. N2: "S rises with length for Claude and MiniMax and declines for the others, most for Gemini (0.91 to 0.70), whose uniform curve declines more (0.48 to 0.21)"

length_scaling, S at 32K → 128K:

| Reader | S 32K → 128K | Direction |
|---|---|---|
| Claude | 0.858 → 0.967 | up |
| MiniMax | 0.396 → 0.563 | up |
| Gemini | 0.913 → 0.704 | down (−0.21, largest) |
| GPT | 0.592 → 0.500 | down |
| Qwen | 0.600 → 0.537 | down |
| Llama | 0.504 → 0.471 | down |

Llama is non-monotone (0.537 at 64K), but the comparison is endpoint to endpoint. Gemini under A: 0.475 → 0.213, a drop of 0.26, which exceeds 0.21. The values agree with tab/app_length.tex as checked in round 2. RESOLVED.

## 4. Other changed sentences (diff vs HEAD)

- **3_method:** a rephrasing of "about 1 s for 32K and 4 s for 128K". The numbers are unchanged.
- **6_conclusion, Limitations:** "trails plain text by 0.21 recall". NIQ mean X−T over the 5 readers is −0.2134. MATCH.
- **6_conclusion, Conclusion:** the first sentence was shortened and contains no numbers. The rest is unchanged.
- **4_setup and 5_results:** covered in items 1 and 3.

## 5. Page limit

`pdftotext` shows §6 "Limitations and Conclusion" ending on page 8, with "References" as the first heading on page 9 (15 pages total). The PDF contains the new text: the "fewer than 100 of roughly 35,000" sentence, "rises with length", and "Llama at 16K". PASS.
