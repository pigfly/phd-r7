"""Zero-cost diagnosis of the real-data prose cost (run3_real): which probes fail in arm C, and does it depend on
sharing a line with an enlarged token / probe position?  usage: python3 diag_prose.py [run3_real]"""
import json, re
from collections import defaultdict
from pathlib import Path
import make_items as M
import sys; RUN = sys.argv[1] if len(sys.argv) > 1 else "run3_real"; M.REAL = "real" in RUN
HERE = Path(__file__).parent; run = HERE / RUN
gt = {g["item"]: g for g in json.loads((run / "gt.json").read_text())}
man = json.loads((run / "manifest.json").read_text())
preds = {}
for f in list(run.glob("pred_r*.json")): preds.setdefault("claude", {}).update(json.loads(f.read_text()))
preds["minimax"] = json.loads((run / "pred_minimax.json").read_text())
PROBES = {"codename": "The release codename is", "mascot": "The team mascot is a", "server": "The backup server is named"}

def probe_lines(text, arm, slo, shi):
    units = M.units_uniform(text, slo) if arm == "A" else M.units_word(text, slo, shi)
    lines = M.layout(units)
    strs = ["".join(t for _, t, _ in ln) for ln in lines]
    big = [any(s > slo for _, _, s in ln) for ln in lines]
    flat = "".join(strs); offs = [0]
    for s in strs: offs.append(offs[-1] + len(s))
    out = {}
    for k, p in PROBES.items():
        i = flat.find(p); j = i + len(p) + 12
        L = [n for n in range(len(strs)) if offs[n] < j and offs[n + 1] > i]
        out[k] = dict(big=any(big[n] for n in L), split=len(L) > 1, line=L[0] / len(strs))
    return out

agg = defaultdict(lambda: [0, 0])
for rd, P in preds.items():
    for m in man:
        p = P.get(m["name"] + ".png"); g = gt[m["item"]]
        if p is None: continue
        info = probe_lines(g["text"], m["arm"], m["s_lo"], m["s_hi"])
        for k, inf in info.items():
            ok = p.get(k, "").strip().strip(".").lower() == g[k]
            for key in [(rd, m["arm"], "all"), (rd, m["arm"], f"bigline={inf['big']}"), (rd, m["arm"], f"split={inf['split']}"),
                        (rd, m["arm"], "pos=" + ("top" if inf["line"] < .5 else "bottom"))]:
                agg[key][0] += ok; agg[key][1] += 1
            if not ok and m["arm"] == "C": agg[(rd, "C", "wrong:" + ("empty" if not p.get(k) else "other"))][0] += 1
for k in sorted(agg): print(k, f"{agg[k][0]}/{agg[k][1]}" if agg[k][1] else agg[k][0], f"{agg[k][0]/agg[k][1]:.2f}" if agg[k][1] else "")
