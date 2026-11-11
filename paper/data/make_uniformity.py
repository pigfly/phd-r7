"""Entropy-uniformity numbers for the paper (from thoughts/exp/real/analysis_uniformity.json and analysis_half.json).
usage: python3 paper/data/make_uniformity.py -> paper/tab/app_uniformity.tex, paper/data/uniformity_macros.tex"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; EXP = ROOT.parent / "thoughts" / "exp" / "real"
U = json.loads((EXP / "analysis_uniformity.json").read_text())
ARM = {"A": "COC", "U": "font search", "Z": "downsample", "R": "random words", "B": "box", "H": "half", "S": "\\name"}
SET = {"tab1_s5": "16K, 5\\,px", "tab1_s6": "16K, 6\\,px", "s8": "32K, 8\\,px", "s10": "32K, 10\\,px",
       "len32k": "32K, 6\\,px", "len64k": "64K, 6\\,px", "len128k": "128K, 6\\,px"}
ORDER = "AUZBRHS"

def p_tex(p):
    m, e = f"{p:.0e}".split("e"); return f"{m}\\times10^{{{int(e)}}}"

eq, al, it = U["spearman_eq16k"], U["spearman_all"], U["spearman_items_eq16k"]
mac = {"UrhoEq": f"{eq['rho']:.2f}", "UpEq": p_tex(eq["p"]), "UnEq": str(eq["n"]), "UrhoAll": f"{al['rho']:.2f}", "UnAll": str(al["n"]),
       "UrhoItems": f"{it['rho']:.2f}", "UnItems": f"{it['n']:,}".replace(",", "{,}"),
       "UrhoMin": f"{min(v['spearman_eq16k']['rho'] for v in U['variants'].values()):.2f}",
       "UrhoMax": f"{max(v['spearman_eq16k']['rho'] for v in U['variants'].values()):.2f}",
       "UtriMax": f"{max(abs(v['rho']) for v in U['triage'].values()):.2f}"}
(ROOT / "data" / "uniformity_macros.tex").write_text("".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in mac.items()))

pts = sorted(U["points"], key=lambda p: (list(SET).index(p["setting"]), ORDER.index(p["arm"])))
rows, last = [], None
for p in pts:
    rows.append(f"{SET[p['setting']] if p['setting'] != last else ''} & {ARM[p['arm']]} & {p['U']:.3f} & {p['lam']:.1f} & {p['recall']:.2f} \\\\")
    if p["setting"] != last and last is not None: rows[-1] = "\\midrule\n" + rows[-1]
    last = p["setting"]
VN = {"top": "top 160 windows", "tail": "top 1\\% of windows", "max": "maximum window"}
vrows = []
for m, v in U["variants"].items():
    kind = "top" if m.startswith("Utop") else ("tail" if m.startswith("Utail") else "max"); n = m.lstrip("Utopailmx")
    vrows.append((kind, int(n), f"{VN[kind]} & {n} & {v['spearman_eq16k']['rho']:.2f} & {v['spearman_all']['rho']:.2f} & {v['spearman_items_eq16k']['rho']:.2f} \\\\"))
vrows = [r for _, _, r in sorted(vrows, key=lambda x: (["top", "tail", "max"].index(x[0]), x[1]))]
tri = U["triage"]
(ROOT / "tab" / "app_uniformity.tex").write_text(r"""\begin{table}[!htbp]
\centering
\caption{\textbf{Entropy uniformity and recall for every arm and setting.} $\U$ (\cref{eq:uniformity}, $n{=}48$, top 160 windows), mean load $\bar\ell$ in bits per vision token, and recall averaged over the five non-Claude readers. Within each setting all arms share one budget.}
\label{tab:app_uniformity}
\footnotesize
\begin{tabular}{l l c c c}
\toprule
Setting & Arm & $\U$ & $\bar\ell$ & Recall \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}

\begin{table}[!htbp]
\centering
\caption{\textbf{Robustness of the recall--uniformity correlation} to the window length $n$ and the tail statistic. Spearman $\rho$ over the 13 arm--budget points at 16K characters (equal budget), over all 25 points, and over single images at 16K (reader-averaged recall).}
\label{tab:app_urobust}
\footnotesize
\begin{tabular}{l c c c c}
\toprule
Tail statistic & $n$ & $\rho$ (16K points) & $\rho$ (all points) & $\rho$ (images) \\
\midrule
""" + "\n".join(vrows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")
print(mac); print({k: round(v["rho"], 2) for k, v in tri.items()})
