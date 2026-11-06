"""Appendix tables added after review round 1 (all numbers from thoughts/exp/real/analysis_* and run manifests).
usage: python3 paper/data/make_appendix_tables.py  -> paper/tab/app_*.tex"""
import json, statistics as St
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; TAB = ROOT / "tab"; EXP = ROOT.parent / "thoughts" / "exp" / "real"
RS = json.loads((EXP / "analysis_rescore.json").read_text()); PO = json.loads((EXP / "analysis_pooled.json").read_text())
N = json.loads((ROOT / "data" / "numbers.json").read_text())
R5 = ["gemini-3.5-flash-lite", "gpt-6-luna", "qwen3-vl-235b-a22b-instruct", "llama-4-maverick", "minimax"]
SH = {"gemini-3.5-flash-lite": "Gemini", "gpt-6-luna": "GPT", "qwen3-vl-235b-a22b-instruct": "Qwen", "llama-4-maverick": "Llama", "minimax": "MiniMax"}
def avg(xs):
    xs = [x for x in xs if x is not None]; return St.mean(xs) if xs else None
def g(run, rd, arm, k):
    a = RS.get(f"{run}|{rd}", {}).get("arms", {}).get(arm); return None if a is None else a.get(k)
def m5(run, arm, k): return avg(g(run, rd, arm, k) for rd in R5)
def b5(run, arm): return avg((g(run, rd, arm, "billed") or None) for rd in R5)
f2 = lambda x: "--" if x is None else f"{x:.2f}"
def table(name, cap, label, cols, header, rows, star=False, size=r"\small", resize=True):
    env = "table"; pos = "!htbp"  # supplementary is one-column
    body = "\\begin{tabular}{" + cols + "}\n\\toprule\n" + header + "\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}"
    if resize: body = "\\fitwidth{%\n" + body + "}"
    (TAB / f"{name}.tex").write_text("\\begin{" + env + "}[" + pos + "]\n\\centering\n\\caption{" + cap + "}\n\\label{" + label + "}\n" + size +
                                     "\n\\setlength{\\tabcolsep}{3pt}\n" + body + "\n\\end{" + env + "}\n")

# ---- 1. full pooled statistics
LAB = {"tab1_s5": "RULER 16K, 5\\,px", "tab1_s6": "RULER 16K, 6\\,px", "length": "RULER 32K--128K, 6\\,px", "density": "density $k\\le16$, 32K",
       "box_s6": "RULER 16K, 6\\,px (box runs)", "s8": "RULER 32K, 8\\,px", "s10": "RULER 32K, 10\\,px", "long_kx": "multi-key 64K--128K",
       "niq2_s5": "natural, flagged, 5\\,px", "niq2_s6": "natural, flagged, 6\\,px", "niq2_s7": "natural, flagged, 7\\,px",
       "niq3_s6": "natural, detector-indep.", "longbench": "LongBench QA (F1)"}
fz = lambda x: "0.00" if abs(x) < 0.005 else f"{x:+.2f}"
def pooled_rows(fams):
    rows = []
    for k in PO:
        fam, cmp, met = k.split("|")
        if fam not in fams or not (fam == "longbench" or met == "recall" or fam.startswith("niq")): continue
        for mm in [met] + (["f1"] if fam != "longbench" and not fam.startswith("niq") else []):
            r = PO[f"{fam}|{cmp}|{mm}"]
            rows.append(f"{LAB[fam] if mm == met else ''} & {cmp.replace('-', '$-$') if mm == met else ''} & {mm if mm != 'f1' else 'F1'} & {fz(r['pooled'])} & "
                        f"[{fz(r['ci_items'][0])}, {fz(r['ci_items'][1])}] & [{fz(r['ci_readers_items'][0])}, {fz(r['ci_readers_items'][1])}] & "
                        f"{r['sig_pos']}/{r['sig_neg']} & {r['sig_pos_holm']}/{r['sig_neg_holm']} & {r['cells']} \\\\")
    return rows
HDR = r"Setting & Comparison & Metric & $\Delta$ & CI$_{\mathrm{item}}$ & CI$_{\mathrm{rd+item}}$ & raw $+/-$ & Holm $+/-$ & cells \\"
CAPN = r" CI$_{\mathrm{item}}$ resamples items within each run with the readers fixed. CI$_{\mathrm{rd+item}}$ also resamples readers (one draw shared by all runs). Cells are counted as significantly positive/negative by per-cell bootstrap, raw and after Holm correction within the row."
table("app_pooled", r"\textbf{All pooled comparisons, RULER at 16K characters} (five non-Claude readers; recall and precision-aware F1)." + CAPN,
      "tab:app_pooled", "l l l r c c c c r", HDR, pooled_rows({"tab1_s5", "tab1_s6", "box_s6"}), star=True, size=r"\footnotesize", resize=False)
table("app_pooled2", r"\textbf{All pooled comparisons, other settings} (five non-Claude readers). On natural strings, recall and F1 coincide. On LongBench, only F1 is defined." + CAPN,
      "tab:app_pooled2", "l l l r c c c c r", HDR, pooled_rows({"length", "s8", "s10", "density", "long_kx", "niq2_s5", "niq2_s6", "niq2_s7", "niq3_s6", "longbench"}),
      star=True, size=r"\footnotesize", resize=False)

# ---- 2. rescoring and anchor leakage (RULER + density + long)
rows = []
SETS = [(f"rbx_s{z}_{t}", f"16K, {z}\\,px, {t.replace('_3','').replace('_1','').replace('multi', 'multi-')}") for z in (5, 6) for t in ("single_3", "multikey_1", "multivalue")]
SETS += [(f"rdens_k{k}", f"density $k{{=}}{k}$") for k in (1, 4, 16, 64)] + [(f"rv2_c{c}k_multikey_1", f"multi-key {c}K") for c in (64, 128)]
for run, lab in SETS:
    c = [lab]
    for a in "ASKX": c += [f2(m5(run, a, "recall")), f2(m5(run, a, "f1")), f"{m5(run, a, 'nret'):.1f}" if m5(run, a, "nret") is not None else "--"]
    c += [f"{m5(run, 'K', 'nanc'):.1f}", f2(m5(run, "K", "dump")), f2(m5(run, "K", "pick"))]
    rows.append(" & ".join(c) + " \\\\")
hdr = (r"& \multicolumn{3}{c}{A} & \multicolumn{3}{c}{S} & \multicolumn{3}{c}{K} & \multicolumn{3}{c}{X} & \multicolumn{3}{c}{anchor list} \\" "\n"
       r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(lr){8-10}\cmidrule(lr){11-13}\cmidrule(lr){14-16}" "\n"
       r"Setting & rec & F1 & \#ret & rec & F1 & \#ret & rec & F1 & \#ret & rec & F1 & \#ret & \#anc & dump & pick \\")
table("app_rescore", r"\textbf{Precision-aware rescoring and anchor content} (means over five readers). rec: recall; F1: precision-aware F1 over the returned values; \#ret: values returned per item; \#anc: distinct anchors per item; dump: recall of returning every anchor; pick: expected recall of returning as many random anchors as there are gold values. Neither copy baseline looks at the image. On single and multi-value the anchor list contains exactly the needles, so K and X approach the dump baseline. At $k{\ge}4$, several readers return most of the list, which recall rewards and F1 does not.",
      "tab:app_rescore", "l " + "ccc " * 4 + "ccc", hdr, rows, star=True, size=r"\footnotesize")

# ---- 3. controls and milder budgets, per reader
rows = []
for rd in R5:
    c = [SH[rd]]
    c += [f2(avg(g(f"rv2_box_s6_{t}", rd, a, "recall") for t in ("single_3", "multikey_1", "multivalue"))) for a in "ABS"]
    for z in (8, 10): c += [f2(avg(g(f"rv2_s{z}_c32k_{t}", rd, a, "recall") for t in ("single_3", "multikey_1"))) for a in "AUSKX"]
    rows.append(" & ".join(c) + " \\\\")
c = ["\\textit{Mean}"]
c += [f2(avg(m5(f"rv2_box_s6_{t}", a, "recall") for t in ("single_3", "multikey_1", "multivalue"))) for a in "ABS"]
for z in (8, 10): c += [f2(avg(m5(f"rv2_s{z}_c32k_{t}", a, "recall") for t in ("single_3", "multikey_1"))) for a in "AUSKX"]
rows += ["\\midrule", " & ".join(c) + " \\\\"]
c = ["\\textit{Billed}"] + [f"{avg(b5(f'rv2_box_s6_{t}', a) for t in ('single_3', 'multikey_1', 'multivalue')):.0f}" for a in "ABS"]
for z in (8, 10): c += [f"{avg(b5(f'rv2_s{z}_c32k_{t}', a) for t in ('single_3', 'multikey_1')):.0f}" for a in "AUSKX"]
rows.append(" & ".join(c) + " \\\\")
hdr = (r"& \multicolumn{3}{c}{Box control, 16K, 6\,px} & \multicolumn{5}{c}{32K, 8\,px} & \multicolumn{5}{c}{32K, 10\,px} \\" "\n"
       r"\cmidrule(lr){2-4}\cmidrule(lr){5-9}\cmidrule(lr){10-14}" "\n" r"Reader & A & B & S & A & U & S & K & X & A & U & S & K & X \\")
table("app_controls", r"\textbf{Salience control and milder budgets} (recall per reader). The box control averages three RULER tasks on a fresh sample of 25 items each; the milder budgets average single and multi-key. B boxes the flagged strings without enlarging them.",
      "tab:app_controls", "l ccc ccccc ccccc", hdr, rows, star=True)

# ---- 4. natural-identifier frontier and detector-independent set, per reader
rows = []
for rd in R5:
    c = [SH[rd]]
    for z in (5, 6, 7): c += [f2(g(f"niq2_s{z}", rd, a, "recall")) for a in "ASKX"]
    rows.append(" & ".join(c) + " \\\\")
c = ["\\textit{Mean}"]
for z in (5, 6, 7): c += [f2(m5(f"niq2_s{z}", a, "recall")) for a in "ASKX"]
rows += ["\\midrule", " & ".join(c) + " \\\\"]
c = ["\\textit{Billed}"]
for z in (5, 6, 7): c += [f"{b5(f'niq2_s{z}', a):.0f}" for a in "ASKX"]
rows.append(" & ".join(c) + " \\\\")
hdr = (r"& \multicolumn{4}{c}{5\,px} & \multicolumn{4}{c}{6\,px} & \multicolumn{4}{c}{7\,px} \\" "\n"
       r"\cmidrule(lr){2-5}\cmidrule(lr){6-9}\cmidrule(lr){10-13}" "\n" r"Reader & A & S & K & X & A & S & K & X & A & S & K & X \\")
table("app_niqfront", r"\textbf{Natural identifiers at three budgets} (flagged targets, $N{=}60$, recall). Billed tokens average the four readers that report usage. X is at or above K at every budget and costs the same as K at 5\,px, where prose cannot shrink.",
      "tab:app_niqfront", "l cccc cccc cccc", hdr, rows, star=True)

# ---- 5. long-context anchors, per reader
rows = []
for rd in R5 + ["mean"]:
    if rd == "mean": rows.append("\\midrule")
    c = [SH[rd] if rd != "mean" else "\\textit{Mean}"]
    for C in (64, 128):
        run = f"rv2_c{C}k_multikey_1"
        c += [f2(g(run, rd, a, k) if rd != "mean" else m5(run, a, k)) for a in "ASKX" for k in ("recall", "f1")]
    rows.append(" & ".join(c) + " \\\\")
c = ["\\textit{Billed}"]
for C in (64, 128): c += [f"\\multicolumn{{2}}{{c}}{{{b5(f'rv2_c{C}k_multikey_1', a):.0f}}}" for a in "ASKX"]
rows.append(" & ".join(c) + " \\\\")
hdr = (r"& \multicolumn{8}{c}{64K characters} & \multicolumn{8}{c}{128K characters} \\" "\n"
       r"\cmidrule(lr){2-9}\cmidrule(lr){10-17}" "\n"
       r"& \multicolumn{2}{c}{A} & \multicolumn{2}{c}{S} & \multicolumn{2}{c}{K} & \multicolumn{2}{c}{X} & \multicolumn{2}{c}{A} & \multicolumn{2}{c}{S} & \multicolumn{2}{c}{K} & \multicolumn{2}{c}{X} \\" "\n"
       r"Reader & rec & F1 & rec & F1 & rec & F1 & rec & F1 & rec & F1 & rec & F1 & rec & F1 & rec & F1 \\")
table("app_longkx", r"\textbf{Anchors at long context} (RULER multi-key, 6\,px, $N{=}20$; recall and precision-aware F1). Allocation makes X 29--31\% cheaper than K, but under F1 the three arms S, K, and X are indistinguishable.",
      "tab:app_longkx", "l " + "cc" * 8, hdr, rows, star=True, size=r"\footnotesize", resize=False)

# ---- 6. near-miss (silent) errors on RULER 16K, five readers
t1 = N["table1_baselines_ruler16k"]; rows = []
for rd in R5:
    c = [SH[rd]]
    for d in ("s5", "s6"): c += [f2(t1[f"{d}|{rd}"][f"silent_{a}"]) for a in "AUZSK"]
    rows.append(" & ".join(c) + " \\\\")
c = ["\\textit{Mean}"]
for d in ("s5", "s6"): c += [f2(avg(t1[f"{d}|{rd}"][f"silent_{a}"] for rd in R5)) for a in "AUZSK"]
rows += ["\\midrule", " & ".join(c) + " \\\\"]
hdr = (r"& \multicolumn{5}{c}{5\,px budget} & \multicolumn{5}{c}{6\,px budget} \\" "\n" r"\cmidrule(lr){2-6}\cmidrule(lr){7-11}" "\n"
       r"Reader & A & U & Z & S & K & A & U & Z & S & K \\")
table("app_silent", r"\textbf{Well-formed near-misses} on RULER (16K): fraction of gold values for which the reader returned a different string of the same length with at least 60\% character similarity. Allocation does not reduce this rate; anchors nearly remove it.",
      "tab:app_silent", "l ccccc ccccc", hdr, rows, size=r"\footnotesize", resize=False)

# ---- 7. allocation statistics from manifests
rows = []
for run, lab in [("rbx_s5_single_3", "16K, 5\\,px"), ("rbx_s6_single_3", "16K, 6\\,px"), ("rlong_c32k_multikey_1", "32K, 6\\,px"),
                 ("rlong_c128k_multikey_1", "128K, 6\\,px"), ("rv2_s8_c32k_multikey_1", "32K, 8\\,px"), ("rv2_s10_c32k_multikey_1", "32K, 10\\,px"),
                 ("rdens_k16", "density $k{=}16$"), ("rdens_k256", "density $k{=}256$"), ("niq2_s6", "natural, flagged"), ("lb3_s6_mfqa", "LongBench MFQA"), ("lb3_s6_hotpot", "LongBench HotpotQA")]:
    man = json.loads((EXP / run / "manifest.json").read_text()); S = [m for m in man if m["arm"] == "S"]; A = {m["item"]: m for m in man if m["arm"] == "A"}
    cnt = Counter((m["s_lo"], m["s_hi"]) for m in S); top = ", ".join(f"{lo}/{hi} ({n})" for (lo, hi), n in cnt.most_common(3))
    rows.append(f"{lab} & {len(S)} & {top} & {St.mean(m['vtok'] / A[m['item']]['vtok'] for m in S):.2f} & {St.mean(m['extra'] == -1 for m in S):.2f} \\\\")
table("app_alloc", r"\textbf{Sizes chosen by the allocation} (prose/flagged glyph height in px, with the number of documents), vision tokens of S relative to the uniform budget, and the fraction of documents that needed the $-$1\,px leading fallback.",
      "tab:app_alloc", "l r l c c", r"Setting & docs & most frequent $s_{\mathrm{lo}}/s_{\mathrm{hi}}$ & $v(S)/B$ & fallback \\", rows, size=r"\footnotesize", resize=False)
print("appendix tables written")
