"""Generate LaTeX tables from paper/data/numbers.json (no hand-copied numbers).
usage: python3 paper/data/make_tables.py  -> paper/tab/*.tex"""
import json, statistics as St
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; N = json.loads((ROOT / "data" / "numbers.json").read_text())
TAB = ROOT / "tab"; TAB.mkdir(exist_ok=True)
NM = N["reader_names"]; RD = list(NM)
SHORT = {"claude-sonnet-5.5": "Claude Sonnet 5.5", "gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite", "gpt-6-luna": "GPT-6 Luna",
         "qwen3-vl-235b-a22b-instruct": "Qwen3-VL-235B", "llama-4-maverick": "Llama 4 Maverick", "minimax": "MiniMax-M3"}

def fmt(x, best=False, second=False, d=2):
    s = f"{x:.{d}f}"
    return f"\\textbf{{{s}}}" if best else (f"\\underline{{{s}}}" if second else s)

# ---------------- Table 1: equal-budget arms (A,U,Z,S) + anchors K, both densities
t = N["table1_baselines_ruler16k"]
rows = []
for rd in RD + ["mean"]:
    cells = []
    for d in ("s5", "s6"):
        v = t[f"{d}|{rd}"]; eq = {a: v[a] for a in "AUZS"}; mx = max(eq.values())
        srt = sorted(set(eq.values()), reverse=True); sec = srt[1] if len(srt) > 1 else None
        cells += [fmt(v[a], v[a] == mx and mx > 0) for a in "AUZS"] + [f"\\textcolor{{gray}}{{{v['K']:.2f}}}"]
    name = "\\textit{Mean}" if rd == "mean" else SHORT[rd]
    if rd == "mean": rows.append("\\midrule")
    rows.append(f"{name} & " + " & ".join(cells) + " \\\\")
cost = []
for d in ("s5", "s6"):
    v = t[f"{d}|mean"]; cost += [f"{v['billed_'+a]:.0f}" for a in "AUZS"] + [f"\\textcolor{{gray}}{{{v['billed_K']:.0f}}}"]
rows.append("\\textit{Billed tokens} & " + " & ".join(cost) + " \\\\")
(TAB / "baselines.tex").write_text(r"""\begin{table*}[t]
\centering
\caption{\textbf{Equal-budget comparison on RULER needle retrieval (16K characters).} Recall averaged over three NIAH tasks ($N{=}25$ each) per reader, at two rendering densities (uniform 5\,px $\approx$ 21 and 6\,px $\approx$ 14 characters per vision token). A, U, Z, and S are images with the same vision-token budget; \textbf{bold} marks the best among them. K adds anchors (verbatim text copies of the flagged strings) to A and is shown in gray because it spends extra text tokens. The last row is the provider-billed prompt-token count averaged over the readers that report usage. Hazard-aware rendering (S) is significantly worse than U or Z in none of the 72 paired comparisons (36 reader$\times$task$\times$density cells $\times$ 2 baselines) and significantly better in 63.}
\label{tab:baselines}
\small
\setlength{\tabcolsep}{4.2pt}
\begin{tabular}{l ccccc ccccc}
\toprule
& \multicolumn{5}{c}{5\,px budget ($\approx$21 chars/vtok)} & \multicolumn{5}{c}{6\,px budget ($\approx$14 chars/vtok)} \\
\cmidrule(lr){2-6}\cmidrule(lr){7-11}
Reader & A & U & Z & S (ours) & \textcolor{gray}{K} & A & U & Z & S (ours) & \textcolor{gray}{K} \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table*}
""")

# ---------------- Table 2: LongBench held-out QA (A,S,K,X)
lb = N["longbench_lb3"]
rows = []
def star(d): return "$^{\\dagger}$" if d[2] < 0 else ("$^{\\ast}$" if d[1] > 0 else "")
for rd in RD:
    cells = []
    for task in ("mfqa", "hotpot"):
        v = lb[f"lb3_s6_{task}|{rd}"]; a = v["arms"]; dd = v["diffs"]
        cells += [f"{a['A']['f1']:.2f}"] + [f"{a[x]['f1']:.2f}{star(dd[x+'-A'])}" for x in "SKX"]
    rows.append(f"{SHORT[rd]} & " + " & ".join(cells) + " \\\\")
mean = []
for task in ("mfqa", "hotpot"):
    vs = [lb[f"lb3_s6_{task}|{rd}"]["arms"] for rd in RD]
    mean += [f"{St.mean(v[x]['f1'] for v in vs):.2f}" for x in "ASKX"]
rows += ["\\midrule", "\\textit{Mean} & " + " & ".join(mean) + " \\\\"]
(TAB / "longbench.tex").write_text(r"""\begin{table}[t]
\centering
\caption{\textbf{Reallocation does not hurt comprehension.} LongBench QA F1 on held-out samples ($N{=}50$ per task, contexts $\le$40K characters, 6\,px budget). $^{\ast}$/$^{\dagger}$: paired 95\% CI vs.\ uniform rendering (A) above/below zero. Ours + anchors (X) has no significantly negative cell.}
\label{tab:longbench}
\small
\setlength{\tabcolsep}{2.6pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{l cccc cccc}
\toprule
& \multicolumn{4}{c}{MultiFieldQA-en} & \multicolumn{4}{c}{HotpotQA} \\
\cmidrule(lr){2-5}\cmidrule(lr){6-9}
Reader & A & S & K & X & A & S & K & X \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}}
\end{table}
""")

# ---------------- Table 3: detector ablation
de = N["detector_ablation"]
lab = {"A": "Uniform (A)", "S": "Ours, regex detector (S)", "O": "Ours, oracle detector", "X": "Ours + anchors, regex (X)", "Y": "Ours + anchors, oracle"}
rows = [f"{lab[a]} & {de['rdet_mv7'][a]:.2f} & {de['rdet_mv4'][a]:.2f} \\\\" + ("\n\\midrule" if a == "A" else "") for a in "ASOXY"]
(TAB / "detector.tex").write_text(r"""\begin{table}[t]
\centering
\caption{\textbf{Detector ablation.} RULER multi-value recall (16K characters, 6\,px budget, $N{=}25$, mean of 5 readers; Claude was not run in this ablation). Seven-digit values are flagged by the regex detector; four-digit values are deliberately not (they collide with years), so the regex arms fall back to uniform rendering.}
\label{tab:detector}
\small
\setlength{\tabcolsep}{5pt}
\begin{tabular}{l cc}
\toprule
& 7-digit values & 4-digit values \\
Arm & (detected) & (missed) \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")
print("tables written:", sorted(p.name for p in TAB.iterdir()))

# ======================= appendix tables =======================
EXP = ROOT.parent / "thoughts" / "exp" / "real"
# A1: length scaling per reader
ls = N["length_scaling"]; rows = []
for rd in RD:
    c = []
    for L in ("32k", "64k", "128k"):
        v = ls[f"{L}|{rd}"]; c += [f"{v['A']:.2f}", f"\\textbf{{{v['S']:.2f}}}"]
    rows.append(f"{SHORT[rd]} & " + " & ".join(c) + " \\\\")
rows += ["\\midrule", "\\textit{Mean} & " + " & ".join(f"{ls[f'{L}|mean'][a]:.2f}" for L in ("32k", "64k", "128k") for a in "AS") + " \\\\"]
(TAB / "app_length.tex").write_text(r"""\begin{table}[h]
\centering\small\setlength{\tabcolsep}{4pt}
\caption{Per-reader recall for the length study (\cref{fig:scaling}).}
\label{tab:app_length}
\begin{tabular}{l cc cc cc}
\toprule
& \multicolumn{2}{c}{32K} & \multicolumn{2}{c}{64K} & \multicolumn{2}{c}{128K} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}
Reader & A & S & A & S & A & S \\
\midrule
""" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")

# A2: density sweep per reader (K vs X)
den = N["density_sweep"]; ks = ["1", "4", "16", "64", "128", "256"]; rows = []
for rd in RD:
    c = []
    for k in ks:
        pr = den[k]["per_reader"].get(rd)
        c.append(f"{pr['K']:.2f}/{pr['X']:.2f}" if pr else "--")
    rows.append(f"{SHORT[rd]} & " + " & ".join(c) + " \\\\")
(TAB / "app_density.tex").write_text(r"""\begin{table}[h]
\centering\small\setlength{\tabcolsep}{3pt}
\caption{Per-reader recall in the hazard-density sweep, K/X (anchors on uniform rendering / on our rendering).}
\label{tab:app_density}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{l cccccc}
\toprule
Reader & $k{=}1$ & 4 & 16 & 64 & 128 & 256 \\
\midrule
""" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}}\n\\end{table}\n")

# A3: real corpora
rc = N["real_density"]["corpora"]; rows = []
for name, v in rc.items():
    nm = name.replace("longbench/", "LB/").replace("_", "\\_")
    rows.append(f"{nm} & {v['n']} & {v['flag_per_1k']:.2f} & {v['r_median']:.2f} & {v['r_p90']:.2f} & {100*v['frac_X']:.0f}\\% & {v['cost_rel']:.2f} \\\\")
fit = N["real_density"]["fit"]
(TAB / "app_corpora.tex").write_text(r"""\begin{table}[h]
\centering\small\setlength{\tabcolsep}{3.5pt}
\caption{Routing profile of real corpora (32K-character chunks, $\tau{=}0.3$). Flags per 1K characters, median and 90th-percentile routing ratio $r$, share routed to image+anchors (X), and estimated cost relative to plain text. Text tokens are estimated with a linear fit to billed text-only reads (""" + f"{fit[0]:.3f}" + r""" tokens per ordinary and """ + f"{fit[1]:.3f}" + r""" per flagged character; mean absolute relative error """ + f"{100*fit[2]:.1f}" + r"""\%).}
\label{tab:app_corpora}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{l c c c c c c}
\toprule
Corpus & $n$ & flags/1K & $r$ med & $r$ p90 & $\to$X & cost/T \\
\midrule
""" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}}\n\\end{table}\n")

# A4: Claude subagent reader
cl = N["claude_subagent"]; rows = []
for k, v in cl["per_k"].items():
    rows.append(f"{k} & {v['X']:.2f} & {v['K']:.2f} & {v['T']:.2f} & {v['costX']:.2f} & {v['costK']:.2f} \\\\")
(TAB / "app_claude.tex").write_text(r"""\begin{table}[h]
\centering\small\setlength{\tabcolsep}{4pt}
\caption{Additional Claude reader (agent interface, one item per form per agent; $N{=}10$ per cell). Recall and estimated cost relative to plain text.}
\label{tab:app_claude}
\begin{tabular}{c ccc cc}
\toprule
$k$ & X & K & T & cost X/T & cost K/T \\
\midrule
""" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")

# A5: short-context study (synthetic and real 1.6K-char items), C-A on ids and prose
ms = json.loads((EXP / "analysis_run3_s5_run3_s6_run3_real_run4_real.json").read_text())
cond = [("run3_s5", "synthetic, 21"), ("run3_s6", "synthetic, 14"), ("run3_real", "manifests, 14 (a)"), ("run4_real", "manifests, 14 (b)")]
rows = []
for rd in RD:
    c = []
    for run, _ in cond:
        v = ms.get(f"{run}|{rd}")
        if not v or "C-A:ids" not in v["diffs"]: c += ["--", "--"]; continue
        di, dp = v["diffs"]["C-A:ids"], v["diffs"]["C-A:prose"]
        mark = lambda d: d[0] if d is None else (f"{d[0]:+.2f}" + ("$^{\\ast}$" if d[1] > 0 else ("$^{\\dagger}$" if d[2] < 0 else "")))
        c += [mark(di), mark(dp)]
    rows.append(f"{SHORT[rd]} & " + " & ".join(c) + " \\\\")
(TAB / "app_short.tex").write_text(r"""\begin{table*}[h]
\centering\small\setlength{\tabcolsep}{4pt}
\caption{Short documents ($\approx$1.6K characters, one image, $N{=}30$). Difference between word-wrapped reallocation and uniform rendering in identifier exact-match (ids) and in accuracy on three prose probes (prose); column headers give data and characters per vision token. $^{\ast}$/$^{\dagger}$: 95\% CI above/below zero.}
\label{tab:app_short}
\resizebox{\textwidth}{!}{%
\begin{tabular}{l cc cc cc cc}
\toprule
& \multicolumn{2}{c}{""" + cond[0][1] + r"""} & \multicolumn{2}{c}{""" + cond[1][1] + r"""} & \multicolumn{2}{c}{""" + cond[2][1] + r"""} & \multicolumn{2}{c}{""" + cond[3][1] + r"""} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}\cmidrule(lr){8-9}
Reader & ids & prose & ids & prose & ids & prose & ids & prose \\
\midrule
""" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}}\n\\end{table*}\n")
print("appendix tables written")
