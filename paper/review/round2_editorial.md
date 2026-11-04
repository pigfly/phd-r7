# Stage 3' — Re-review Decision (Round 2)

**Decision: MINOR REVISION.** Same five role-separated Claude seats, fresh contexts, with no peer-output visibility before commitment. NOT_CALIBRATED.

| Seat | Recommendation | Round-1 items not fully resolved | New issues (C/M/m) |
|---|---|---|---|
| Journal-Fit | Minor (borderline Accept) | 1 unresolved, 5 partial | 0/1/4 |
| R1 Methodology | Minor | 1 CRIT partial (no decoy control); 3 MAJOR; 4 MINOR | 0/1/7 |
| R2 Domain | Minor (borderline Major) | 2 unresolved (trained compressor; exact match), 5 partial | 0/1/4 |
| R3 Perspective | Minor | 7 (mostly declined deployment experiments, accepted as limitations) | 0/1/3 |
| Devil's Advocate | Narrowed core claim survives | 0 unresolved, 4 partial | 0/2/3 |

**Round-1 DA CRITICAL C1 (attribution):** RESOLVED. Every seat judged the anonymous citation and the narrowed contribution adequate.

## Consensus residual issues (all textual; no new experiments required)
1. **The 64K/128K claim that X matches K at about 30% fewer tokens** relies on multi-key recall, which §5.5 itself labels copying. Under F1, X ≈ K ≈ S (≈0.38), so the saving comes from allocation alone (EIC N1, R1 N1, R3 N1, DA). → Restate it in F1 terms, or credit the saving to S.
2. **Unconditioned claims in the abstract, intro and conclusion.** "Doubles natural-identifier recall" and "matches or exceeds K" hold only for flagged targets. On detector-independent targets the effects are −0.01 and −0.08 (EIC N2, DA, R2). → Add the condition.
3. **Selective reporting in Table 2.** Only the positive X−K row appears (DA, R1 N3). → Report all X−K rows, including density and long-context F1.
4. **Statistics bug (R1 N2).** The cluster bootstrap resamples readers independently within each run instead of sharing one reader draw across runs. → Fix `stats_pooled.py` and regenerate. B−A and X−K (6 px, F1) may then touch 0; word them accordingly.
5. **Reader-set leftovers.** Fig. 5 and Table 5 still use six-reader means; the Table 4 cost row averages four readers but does not say so; the abstract says five readers while the setup lists six (EIC N4, R1 N6, R3 N3/N4).
6. **Numeric slips.** The X−K frontier gap is 0.02–0.05; X and K cost the same at 5 px; "6.4 anchors" counts duplicates (5.3 unique); the box-control CI bound; the cacheability claim needs qualifying (anchors are placed after the question; caching is untested); AGAR uses "middle-to-late-layer" attention.

## Declined or accepted as limitations (no action)
- Trained compressor / pruning / FocusVTC comparison point (R2 W1, EIC W2): R2 still lists this as the main barrier to Accept. The author decided on scope at the Stage 3 checkpoint.
- Latency, caching, multilingual (R3): accepted as limitations.
- Decoy-anchor control, non-inferiority test, repeat runs, snapshot IDs (R1): MINOR to MAJOR residuals. The author may add a non-inferiority statement cheaply from existing data.

Next per state machine: Minor → apply the textual fixes above → Stage 4.5 final integrity.
