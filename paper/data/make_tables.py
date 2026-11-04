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

# Tables 1 (baselines), 2 (LongBench), NIQ and pooled effects: see the revision block at the end.

# ---------------- Table 3: detector ablation
de = N["detector_ablation"]
lab = {"A": "Uniform (A)", "S": "Ours, regex detector (S)", "O": "Ours, oracle detector", "X": "Ours + anchors, regex (X)", "Y": "Ours + anchors, oracle"}
rows = [f"{lab[a]} & {de['rdet_mv7'][a]:.2f} & {de['rdet_mv4'][a]:.2f} \\\\" + ("\n\\midrule" if a == "A" else "") for a in "ASOXY"]
(TAB / "detector.tex").write_text(r"""\begin{table}[h]
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
rows += ["\\midrule", "\\textit{Mean (5 readers, excl.\\ Claude)} & " + " & ".join(f"{St.mean(ls[f'{L}|{r}'][a] for r in RD if r != 'claude-sonnet-5.5'):.2f}" for L in ("32k", "64k", "128k") for a in "AS") + " \\\\"]
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




# ======================= revision (review round 1): fixed 5-reader means, F1, text references, pooled effects
R5 = [r for r in RD if r != "claude-sonnet-5.5"]
RV = N["revision_5readers"]; PO = N["pooled"]
def avg(xs): xs = [x for x in xs if x is not None]; return St.mean(xs) if xs else None
TASKS3 = ("single_3", "multikey_1", "multivalue")

# ---------------- Table 1: equal-budget images (A,U,Z,R,S) and with anchors (K,X)
t = N["table1_baselines_ruler16k"]
def cell(v, best):
    if v is None: return "--"
    return f"\\textbf{{{v:.2f}}}" if (best is not None and abs(v - best) < 1e-9 and v > 0) else f"{v:.2f}"
rows = []
for rd in RD:
    cells = []
    for d in ("s5", "s6"):
        v = t[f"{d}|{rd}"]
        b1 = max(v[a] for a in "AUZRS" if v[a] is not None); b2 = max(v[a] for a in "KX" if v[a] is not None)
        cells += [cell(v[a], b1) for a in "AUZRS"] + [cell(v[a], b2) for a in "KX"]
    rows.append(SHORT[rd] + ("$^{\\ddagger}$" if rd == "claude-sonnet-5.5" else "") + " & " + " & ".join(cells) + " \\\\")
rows.append("\\midrule")
mr, mf, mb = [], [], []
for d in ("s5", "s6"):
    rec = {a: avg(t[f"{d}|{rd}"][a] for rd in R5) for a in "AUZRSKX"}
    b1 = max(rec[a] for a in "AUZRS"); b2 = max(rec[a] for a in "KX")
    mr += [cell(rec[a], b1) for a in "AUZRS"] + [cell(rec[a], b2) for a in "KX"]
    f1 = {a: avg(RV[f"rbx_{d}_{k}"][a]["f1"] for k in TASKS3) if a != "R" else avg(N["rescore"][f"rabl2_{d}_{k}|{rd}"]["arms"]["R"]["f1"] for k in TASKS3 for rd in R5 if f"rabl2_{d}_{k}|{rd}" in N["rescore"]) for a in "AUZRSKX"}
    b1 = max(f1[a] for a in "AUZRS"); b2 = max(f1[a] for a in "KX")
    mf += [cell(f1[a], b1) for a in "AUZRS"] + [cell(f1[a], b2) for a in "KX"]
    mb += [f"{(avg(RV[f'rbx_{d}_{k}'][a]['billed'] for k in TASKS3) if a != 'R' else t[f'{d}|mean']['billed_R']):.0f}" for a in "AUZRSKX"]
rows += ["\\textit{Mean recall} & " + " & ".join(mr) + " \\\\", "\\textit{Mean F1} & " + " & ".join(mf) + " \\\\",
         "\\textit{Billed tokens} & " + " & ".join(mb) + " \\\\"]
pa = lambda f, c: PO[f"{f}|{c}|recall"]
(TAB / "baselines.tex").write_text(r"""\begin{table*}[t]
\centering
\caption{\textbf{Equal-budget comparison on RULER needle retrieval (16K characters).} Recall per reader averaged over three NIAH tasks ($N{=}25$ each), at two budgets (uniform 5\,px $\approx$ 32 and 6\,px $\approx$ 21 characters per vision token). A, U, Z, R, and S are images with the same vision-token budget: uniform, best uniform font/size, render-then-downsample, \emph{random} ordinary words enlarged by our allocation (matched in total length), and flagged strings enlarged (ours). K and X append anchors~\cite{anon2026renderretain} to A and S. \textbf{Bold}: best within each group. Means, F1 (precision-aware: extra returned values count against the reader), and billed tokens are over the five readers other than Claude$^{\ddagger}$, which was not run on R and X. Pooled over tasks and readers, S$-$A is """ + f"+{pa('tab1_s5','S-A')['pooled']:.2f} [{pa('tab1_s5','S-A')['ci_readers_items'][0]:.2f}, {pa('tab1_s5','S-A')['ci_readers_items'][1]:.2f}] at 5\\,px and +{pa('tab1_s6','S-A')['pooled']:.2f} [{pa('tab1_s6','S-A')['ci_readers_items'][0]:.2f}, {pa('tab1_s6','S-A')['ci_readers_items'][1]:.2f}] at 6\\,px (95\\% CI, readers and items resampled; \\cref{{tab:pooled}})." + r""" On these tasks the anchors contain the answer (\cref{sec:anchors}), so K and X measure copying rather than reading.}
\label{tab:baselines}
\small
\setlength{\tabcolsep}{3.4pt}
\resizebox{\textwidth}{!}{%
\begin{tabular}{l ccccc cc ccccc cc}
\toprule
& \multicolumn{7}{c}{5\,px budget ($\approx$32 chars/vtok)} & \multicolumn{7}{c}{6\,px budget ($\approx$21 chars/vtok)} \\
\cmidrule(lr){2-8}\cmidrule(lr){9-15}
& \multicolumn{5}{c}{equal-budget image} & \multicolumn{2}{c}{+ anchors} & \multicolumn{5}{c}{equal-budget image} & \multicolumn{2}{c}{+ anchors} \\
\cmidrule(lr){2-6}\cmidrule(lr){7-8}\cmidrule(lr){9-13}\cmidrule(lr){14-15}
Reader & A & U & Z & R & S (ours) & K & X & A & U & Z & R & S (ours) & K & X \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}}
\end{table*}
""")

# ---------------- Table: pooled effects (5 readers)
def prow(label, fam, cmp, met="recall"):
    r = PO[f"{fam}|{cmp}|{met}"]; lo, hi = r["ci_readers_items"]
    f = lambda x: "0.00" if abs(x) < 0.005 else f"{x:+.2f}"
    return f"{label} & {f(r['pooled'])} & [{f(lo)}, {f(hi)}] & {r['sig_pos_holm']}/{r['cells']} & {r['sig_neg_holm']} \\\\"
prs = [r"\multicolumn{5}{l}{\textit{Targeting vs.\ uniform and alternatives (RULER)}} \\",
       prow("S$-$A, 16K, 5\\,px", "tab1_s5", "S-A"), prow("S$-$A, 16K, 6\\,px", "tab1_s6", "S-A"),
       prow("S$-$A, 32K--128K, 6\\,px", "length", "S-A"),
       prow("S$-$U (font/size search), 6\\,px", "tab1_s6", "S-U"), prow("S$-$R (random words), 6\\,px", "tab1_s6", "S-R"),
       prow("B$-$A (box, no enlargement), 6\\,px", "box_s6", "B-A"), prow("S$-$B, 6\\,px", "box_s6", "S-B"),
       r"\midrule \multicolumn{5}{l}{\textit{Milder budgets (32K)}} \\",
       prow("S$-$A, 8\\,px", "s8", "S-A"), prow("S$-$U, 8\\,px", "s8", "S-U"), prow("S$-$A, 10\\,px", "s10", "S-A"), prow("S$-$U, 10\\,px", "s10", "S-U"),
       r"\midrule \multicolumn{5}{l}{\textit{Natural strings (LongBench documents)}} \\",
       prow("S$-$A, flagged targets", "niq2_s6", "S-A"), prow("S$-$A, detector-independent", "niq3_s6", "S-A"),
       r"\midrule \multicolumn{5}{l}{\textit{Ordinary comprehension (LongBench F1)}} \\",
       prow("S$-$A", "longbench", "S-A", "f1"), prow("X$-$A", "longbench", "X-A", "f1"), prow("X$-$T (plain text)", "longbench", "X-T", "f1"),
       r"\midrule \multicolumn{5}{l}{\textit{Anchors: X$-$K (F1 on RULER, recall on natural strings)}} \\",
       prow("RULER 16K, 5\\,px", "tab1_s5", "X-K", "f1"), prow("RULER 16K, 6\\,px", "tab1_s6", "X-K", "f1"),
       prow("RULER 32K, 8\\,px", "s8", "X-K", "f1"), prow("RULER 32K, 10\\,px", "s10", "X-K", "f1"),
       prow("density $k\\le16$, 32K", "density", "X-K", "f1"), prow("multi-key 64K--128K", "long_kx", "X-K", "f1"),
       prow("natural, flagged, 5\\,px", "niq2_s5", "X-K"), prow("natural, flagged, 6\\,px", "niq2_s6", "X-K"), prow("natural, flagged, 7\\,px", "niq2_s7", "X-K"), prow("natural, detector-indep.", "niq3_s6", "X-K")]
(TAB / "pooled.tex").write_text(r"""\begin{table}[t]
\centering
\caption{\textbf{Pooled effects} over the five non-Claude readers (recall unless noted). CI: 95\% bootstrap resampling readers and items. Sig.: cells (reader $\times$ task) significantly positive after Holm correction within each row; neg.: significantly negative. All X$-$K comparisons we ran are listed.}
\label{tab:pooled}
\small
\setlength{\tabcolsep}{2.5pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{l c c c c}
\toprule
Comparison & $\Delta$ & 95\% CI & sig. & neg. \\
\midrule
""" + "\n".join(prs) + r"""
\bottomrule
\end{tabular}}
\end{table}
""")

# ---------------- Table: LongBench held-out QA with plain text
lb = N["longbench_lb3"]
rows = []
def star(d): return "$^{\\dagger}$" if d[2] < 0 else ("$^{\\ast}$" if d[1] > 0 else "")
for rd in R5:
    cells = []
    for task in ("mfqa", "hotpot"):
        v = lb[f"lb3_s6_{task}|{rd}"]; a = v["arms"]; dd = v["diffs"]
        cells += [f"{a['A']['f1']:.2f}"] + [f"{a[x]['f1']:.2f}{star(dd[x+'-A'])}" for x in "SKX"] + [f"{a['T']['f1']:.2f}"]
    rows.append(f"{SHORT[rd]} & " + " & ".join(cells) + " \\\\")
mean, bil = [], []
for task in ("mfqa", "hotpot"):
    vs = [lb[f"lb3_s6_{task}|{rd}"]["arms"] for rd in R5]
    mean += [f"{St.mean(v[x]['f1'] for v in vs):.2f}" for x in "ASKXT"]
    bil += [f"{St.mean(v[x]['billed'] for v in vs if v[x]['billed']):.0f}" for x in "ASKXT"]
nxt = sum(lb[f"lb3_s6_{t}|{rd}"]["diffs"]["X-T"][2] < 0 for t in ("mfqa", "hotpot") for rd in R5)
rows += ["\\midrule", "\\textit{Mean} & " + " & ".join(mean) + " \\\\", "\\textit{Billed tokens} & " + " & ".join(bil) + " \\\\"]
(TAB / "longbench.tex").write_text(r"""\begin{table}[t]
\centering
\caption{\textbf{Ordinary comprehension.} LongBench QA F1 on held-out samples ($N{=}50$ per task, contexts $\le$40K characters, 6\,px budget, five readers). $^{\ast}$/$^{\dagger}$: paired 95\% CI vs.\ uniform rendering (A) above/below zero. Relative to A, X has no significantly negative cell and S one; every image arm trails plain text T (X$-$T significantly negative in """ + f"{nxt} of {2*len(R5)}" + r""" cells). Billed tokens: four readers that report usage.}
\label{tab:longbench}
\small
\setlength{\tabcolsep}{2.2pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{l ccccc ccccc}
\toprule
& \multicolumn{5}{c}{MultiFieldQA-en} & \multicolumn{5}{c}{HotpotQA} \\
\cmidrule(lr){2-6}\cmidrule(lr){7-11}
Reader & A & S & K & X & T & A & S & K & X & T \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}}
\end{table}
""")

# ---------------- Table: natural identifiers, detector-flagged (niq2) and detector-independent (niq3) targets
rs = N["rescore"]
def g(run, rd, a): return rs[f"{run}|{rd}"]["arms"][a]["recall"]
def sg(run, rd, a):
    d = rs[f"{run}|{rd}"]["diffs"].get(f"{a}-A|recall")
    return "" if d is None else ("$^{\\ast}$" if d[1] > 0 else ("$^{\\dagger}$" if d[2] < 0 else ""))
rows = []
for rd in R5:
    c = [f"{g('niq2_s6', rd, 'A'):.2f}"] + [f"{g('niq2_s6', rd, a):.2f}{sg('niq2_s6', rd, a)}" for a in "SKX"] + [f"{g('niq2_s6', rd, 'T'):.2f}"]
    c += [f"{g('niq3_s6', rd, 'A'):.2f}"] + [f"{g('niq3_s6', rd, a):.2f}{sg('niq3_s6', rd, a)}" for a in "SKX"] + [f"{g('niq3_s6', rd, 'T'):.2f}"]
    rows.append(f"{SHORT[rd]} & " + " & ".join(c) + " \\\\")
mean = [f"{RV[run][a]['recall']:.2f}" for run in ("niq2_s6", "niq3_s6") for a in "ASKXT"]
bil = [f"{RV[run][a]['billed']:.0f}" for run in ("niq2_s6", "niq3_s6") for a in "ASKXT"]
rows += ["\\midrule", "\\textit{Mean} & " + " & ".join(mean) + " \\\\", "\\textit{Billed tokens} & " + " & ".join(bil) + " \\\\"]
(TAB / "niq.tex").write_text(r"""\begin{table}[t]
\centering
\caption{\textbf{Naturally occurring strings.} Exact-copy recall on LongBench documents ($\le$40K characters, 6\,px budget, $N{=}60$ each). \emph{Flagged}: targets the detector flags (report and grant numbers, ISBNs, URLs, \ldots). \emph{Detector-independent}: any digit-bearing token, sampled without the detector (""" + f"{N['niq3_flagged']}" + r"""/60 flagged; mostly short numbers and versions). $^{\ast}$/$^{\dagger}$: paired 95\% CI vs.\ A above/below zero. Billed tokens: four readers that report usage.}
\label{tab:niq}
\small
\setlength{\tabcolsep}{2.2pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{l ccccc ccccc}
\toprule
& \multicolumn{5}{c}{Flagged targets} & \multicolumn{5}{c}{Detector-independent targets} \\
\cmidrule(lr){2-6}\cmidrule(lr){7-11}
Reader & A & S & K & X & T & A & S & K & X & T \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}}
\end{table}
""")
print("revision tables written")
