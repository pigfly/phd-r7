"""Combined analysis across runs and readers.
usage: python3 analyze.py   -> prints tables, writes analysis.json
Reader 'claude' = pred_r*.json (subagents, latin square); 'minimax' = pred_minimax.json."""
import json, random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
RUNS = {"5px": ["run_s5", "run2_s5"], "6px": ["run_s6", "run2_s6"]}
def norm(s): return s.strip().strip(".,;()`'\"").lower()

def load(run, reader):
    d = HERE / run
    files = sorted(d.glob("pred_r*.json")) if reader == "claude" else [d / "pred_minimax.json"]
    pred = {}
    for f in files:
        if f.exists(): pred.update(json.loads(f.read_text()))
    gt = {g["item"]: g for g in json.loads((d / "gt.json").read_text())}
    rows = defaultdict(dict)  # (run,item) -> arm -> metrics
    for m in json.loads((d / "manifest.json").read_text()):
        p = pred.get(m["name"] + ".png") or pred.get(m["name"])
        if p is None: continue
        g = gt[m["item"]]; out = [norm(x) for x in p.get("ids", [])]
        rows[(run, m["item"])][m["arm"]] = dict(
            ids=sum(x["value"] in out for x in g["ids"]) / len(g["ids"]),
            code=float(norm(p.get("codename", "")) == g["codename"]),
            cost=m["vtok"] + m.get("anchor_tok", 0))
    return rows

def boot(d, R, n=10000):
    bs = sorted(sum(R.choice(d) for _ in d) / len(d) for _ in range(n))
    return sum(d) / len(d), bs[int(.025 * n)], bs[int(.975 * n)]

res = {}; R = random.Random(0)
for reader in ["claude", "minimax"]:
    for pt, runs in RUNS.items():
        rows = {}
        for r in runs: rows.update(load(r, reader))
        if not rows: continue
        arms = sorted({a for v in rows.values() for a in v})
        print(f"\n=== {reader} @ {pt}  (items: {len(rows)})")
        tab = {}
        for a in arms:
            v = [x[a] for x in rows.values() if a in x]
            tab[a] = {k: round(sum(e[k] for e in v) / len(v), 3) for k in ("ids", "code", "cost")} | {"n": len(v)}
            print(f"  {a}: ids={tab[a]['ids']:.3f} codename={tab[a]['code']:.3f} cost={tab[a]['cost']:.0f} tok  (n={len(v)})")
        diffs = {}
        for a, b in [("C", "A"), ("P", "A"), ("C", "P"), ("D", "A"), ("D", "C"), ("B", "A")]:
            pairs = [x for x in rows.values() if a in x and b in x]
            if len(pairs) < 5: continue
            for k in ("ids", "code"):
                mu, lo, hi = boot([x[a][k] - x[b][k] for x in pairs], R)
                diffs[f"{a}-{b}:{k}"] = dict(mean=round(mu, 3), ci=[round(lo, 3), round(hi, 3)], n=len(pairs))
                print(f"  {a}-{b} {k:4s}: {mu:+.3f} [{lo:+.3f}, {hi:+.3f}]  n={len(pairs)}")
        res[f"{reader}@{pt}"] = dict(arms=tab, diffs=diffs)
(HERE / "analysis.json").write_text(json.dumps(res, indent=1))
