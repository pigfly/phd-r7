"""Analysis of recall vs entropy uniformity (reads <run>/uniformity.json caches written by uniformity_study.py).
Points = (setting, arm) cells averaged over items and the five readers. Reports Spearman rho at the point level
(and at the item level), per-needle load vs hit, and the 'is reallocation worth it' check (U of the COC image vs gain).
usage: python3 analyze_uniformity.py [metric]   -> analysis_uniformity.json"""
import json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr, pearsonr
from uniformity_study import GROUPS, HERE
from stats_pooled import merged

MET = sys.argv[1] if len(sys.argv) > 1 else "Utail48"

def rows_of(gname):
    runs, arms, size = GROUPS[gname]; parts = runs[0].split("+"); data = merged(runs)[parts[0]]
    cache = HERE / parts[0] / "uniformity.json"
    if not cache.exists(): return []
    U = json.loads(cache.read_text()); out = []
    for key, st in U.items():
        arm, item = key.split("|"); item = int(item)
        if arm not in arms: continue
        rec = [data[rd][item][arm]["recall"] for rd in data if item in data[rd] and arm in data[rd][item]]
        if rec: out.append(dict(group=gname, arm=arm, item=item, recall=float(np.mean(rec)), **st))
    return out

def setting(g):  # groups that share a budget and context length form one setting
    for p in ("tab1_s5", "tab1_s6", "half_s5", "half_s6", "box_s6", "s8", "s10", "len32k", "len64k", "len128k", "niq2", "niq3"):
        if g.startswith(p): return {"half_s5": "tab1_s5", "half_s6": "tab1_s6", "box_s6": "tab1_s6"}.get(p, p)
    return g

def main():
    allrows = [r for g in GROUPS for r in rows_of(g)]
    res = {"metric": MET, "points": []}
    pts = defaultdict(list)
    for r in allrows:
        if r["group"].startswith("niq"): continue
        pts[(setting(r["group"]), r["arm"])].append(r)
    for (st, arm), v in sorted(pts.items()):
        res["points"].append(dict(setting=st, arm=arm, n=len(v), U=float(np.mean([x[MET] for x in v])),
                                  recall=float(np.mean([x["recall"] for x in v])), lam=float(np.mean([x["lam"] for x in v]))))
    P = res["points"]
    # equal-budget settings (16K, 5 and 6 px): every arm shares the budget, so U is the only shape variable
    for name, sel in (("eq16k", lambda p: p["setting"] in ("tab1_s5", "tab1_s6")), ("all", lambda p: True)):
        q = [p for p in P if sel(p)]
        res[f"spearman_{name}"] = dict(zip(("rho", "p"), map(float, spearmanr([p["U"] for p in q], [p["recall"] for p in q]))), n=len(q))
    # within-setting rank correlation (removes budget / length differences), averaged
    ws = []
    for st in sorted({p["setting"] for p in P}):
        q = [p for p in P if p["setting"] == st]
        if len(q) >= 3: ws.append((st, float(spearmanr([p["U"] for p in q], [p["recall"] for p in q])[0]), len(q)))
    res["within_setting"] = ws
    # item level, equal-budget 16K, all arms
    it = [r for r in allrows if setting(r["group"]) in ("tab1_s5", "tab1_s6")]
    res["spearman_items_eq16k"] = dict(zip(("rho", "p"), map(float, spearmanr([r[MET] for r in it], [r["recall"] for r in it]))), n=len(it))
    for p in P: print(f"{p['setting']:8s} {p['arm']}  U={p['U']:.3f}  recall={p['recall']:.2f}  lam={p['lam']:.1f}  n={p['n']}")
    print({k: v for k, v in res.items() if k.startswith("spearman")}); print(res["within_setting"])
    (HERE / "analysis_uniformity.json").write_text(json.dumps(res, indent=1))

if __name__ == "__main__":
    main()
