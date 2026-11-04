"""Precision-aware rescoring of RULER / density / NIQ runs (review RM-2: anchor leakage).
Per run x reader x arm: recall (as in analyze_ruler), precision (fraction of returned values that match a gold value),
F1, exact-set (all gold found and no extra values), mean #returned, mean #unique anchors, gold-in-anchors rate,
and two copy baselines that need no image: 'dump' (return every anchor) and 'pick' (return |gold| anchors at random,
expected recall). usage: python3 rescore.py -> analysis_rescore.json + printed summary"""
import json, random
from collections import defaultdict
from pathlib import Path
from analyze_ruler import failed_read, boot

HERE = Path(__file__).parent
norm = lambda x: str(x).strip().strip(".,;()`'\"").lower()

def match(o, v): return v == o or v in o

def score(p, it):
    out = list(dict.fromkeys(norm(x) for x in p.get("ids", []) if norm(x)))
    gold = [v.lower() for v in it["answers"]]
    hit = [any(match(o, v) for o in out) for v in gold]
    good = [any(match(o, v) for v in gold) for o in out]
    rec = sum(hit) / len(gold); prec = sum(good) / len(out) if out else 0.0
    f1 = 2 * rec * prec / (rec + prec) if rec + prec else 0.0
    return dict(recall=rec, precision=prec, f1=f1, exact=float(all(hit) and all(good)), nret=len(out))

def copy_baselines(anchors, it):
    anc = list(dict.fromkeys(a.lower() for a in anchors)); gold = [v.lower() for v in it["answers"]]
    if not anc: return dict(gin=0.0, dump=0.0, pick=0.0, nanc=0)
    covered = [any(match(a, v) for a in anc) for v in gold]
    dump = sum(covered) / len(gold)
    # pick |gold| anchors uniformly without replacement: expected fraction of gold hit (each covering anchor
    # is drawn with prob min(1, |gold|/|anc|))
    k = min(len(gold), len(anc)); pick = dump * k / len(anc)
    return dict(gin=float(all(covered)), dump=dump, pick=pick, nanc=len(anc))

def load(run):
    """-> {reader: {item: {arm: metrics}}} for one run dir (T from predtext_* files)."""
    items = {it["item"]: it for it in json.loads((run / "gt.json").read_text())["items"]}
    man = json.loads((run / "manifest.json").read_text()); out = {}
    for pf in sorted(run.glob("pred_*.json")):
        reader = pf.stem.replace("pred_or_", "").replace("pred_", ""); pred = json.loads(pf.read_text())
        rows = defaultdict(dict)
        for m in man:
            p = pred.get(m["name"] + ".png")
            if p is None: continue
            fr = failed_read(p)
            if fr == "drop": continue
            if fr == "zero": p = {"ids": []}
            rows[m["item"]][m["arm"]] = score(p, items[m["item"]]) | {"billed": p.get("usage", {}).get("prompt_tokens", 0)}
            if m.get("anchors"): rows[m["item"]][m["arm"]] |= copy_baselines(m["anchors"], items[m["item"]])
        tf = run / pf.name.replace("pred_", "predtext_")
        if tf.exists():
            for k, p in json.loads(tf.read_text()).items():
                fr = failed_read(p)
                if fr == "drop": continue
                rows[int(k[2:-4])]["T"] = score({"ids": []} if fr else p, items[int(k[2:-4])]) | {"billed": p.get("usage", {}).get("prompt_tokens", 0)}
        out[reader] = dict(rows)
    return out

if __name__ == "__main__":
    R = random.Random(0); res = {}
    runs = sorted([*HERE.glob("rbx_*"), *HERE.glob("rabl2_*"), *HERE.glob("rdens_*"), *HERE.glob("niq2_*"), *HERE.glob("niq3_*"), *HERE.glob("rv2_*")])
    for run in runs:
        if not (run / "gt.json").exists(): continue
        for reader, rows in load(run).items():
            arms = sorted({a for r in rows.values() for a in r}); tab = {}
            for a in arms:
                rs = [r[a] for r in rows.values() if a in r]
                tab[a] = {k: round(sum(x.get(k, 0) for x in rs) / len(rs), 3) for k in rs[0]} | {"n": len(rs)}
            diffs = {}
            for a, b in (("X", "K"), ("S", "A"), ("X", "A"), ("K", "A"), ("X", "S"), ("B", "A"), ("S", "B"), ("S", "U"), ("X", "T"), ("K", "T")):
                pr = [r for r in rows.values() if a in r and b in r]
                if len(pr) >= 5:
                    for met in ("recall", "f1", "exact"): diffs[f"{a}-{b}|{met}"] = boot([r[a][met] - r[b][met] for r in pr], R, 4000)
            res[f"{run.name}|{reader}"] = dict(arms=tab, diffs=diffs)
            print(f"{run.name:22s} {reader[:14]:14s} " + " ".join(
                f"{a}:r{t['recall']:.2f}/f{t['f1']:.2f}/e{t['exact']:.2f}/n{t['nret']:.1f}/b{t['billed']:.0f}" + (f"/pick{t['pick']:.2f}" if 'pick' in t else "")
                for a, t in tab.items()))
    (HERE / "analysis_rescore.json").write_text(json.dumps(res, indent=1))
