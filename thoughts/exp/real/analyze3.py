"""Round-3 analysis: 3 prose probes, CD arm (E), real-distribution run, [unreadable] prompt variant.
usage: python3 analyze3.py  -> prints tables, writes analysis3.json"""
import json, random, re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).parent
import sys
RUNS = sys.argv[1:] or ["run3_s5", "run3_s6", "run3_real"]
READERS = {"claude": "pred_r*.json", "minimax": "pred_minimax.json", "minimax_unr": "pred_minimax_unr.json"}
ARM_NAME = {"A": "A uniform", "C": "C hazard", "E": "CD hazard+residual anchors", "D": "D anchors", "P": "C' prose floor", "L": "L C+prose leading", "M": "M mixed wrap"}
PROBES = ("codename", "mascot", "server")

def clean(s): return s.strip().strip(".,;()`'\"")

EXC = ("URLError", "HTTPError", "TimeoutError", "Remote", "IncompleteRead", "ConnectionReset", "JSONDecodeError", "KeyError")
def failed_read(p):
    """None = usable; 'drop' = refusal / empty / transport error (excluded); 'zero' = reader produced unparseable
    output, e.g. degenerate repetition up to max_tokens (scored as an empty answer)."""
    if "error" not in p: return None
    e = (p["error"] or "").strip()
    return "drop" if not e or e.startswith(EXC) else "zero"

def score_item(p, g):
    out = [clean(x) for x in p.get("ids", [])]
    unr = sum("unreadable" in x.lower() for x in out)
    exact = silent = 0
    for d in g["ids"]:
        v = d["value"]
        if d["kind"] in ("b64hash", "relpath"):  # real data: case-sensitive substring (readers may emit the whole manifest line)
            ok = any(v in o for o in out)
            near = (not ok) and any(SequenceMatcher(None, v, o).find_longest_match(0, len(v), 0, len(o)).size >= 0.6 * len(v) for o in out)
        else:
            low = [o.lower() for o in out]; ok = v in low
            near = (not ok) and any(len(o) == len(v) and SequenceMatcher(None, o, v).ratio() >= 0.6 for o in low)
        exact += ok; silent += near
    n = len(g["ids"])
    prose = sum(clean(p.get(k, "")).lower() == g[k] for k in PROBES) / len(PROBES)
    return dict(ids=exact / n, silent=silent / n, abstain=min(unr, n) / n, prose=prose)

def readers_for(run):
    r = dict(READERS)
    for f in sorted((HERE / run).glob("pred_or_*.json")): r[f.stem[len("pred_or_"):]] = f.name
    return r

def load(run, reader):
    d = HERE / run; pred = {}; READERS.update(readers_for(run))
    for f in sorted(d.glob(READERS[reader])): pred.update(json.loads(f.read_text()))
    if not pred: return {}
    gt = {g["item"]: g for g in json.loads((d / "gt.json").read_text())}
    rows = defaultdict(dict)
    for m in json.loads((d / "manifest.json").read_text()):
        p = pred.get(m["name"] + ".png")
        if p is None: continue
        fr = failed_read(p)
        if fr: ERRS.setdefault((run, reader), []).append(m["arm"] + ("" if fr == "drop" else "*"))
        if fr == "drop": continue
        if fr == "zero": p = {"ids": [], "usage": p.get("usage", {})}
        billed = p.get("usage", {}).get("prompt_tokens")
        rows[m["item"]][m["arm"]] = score_item(p, gt[m["item"]]) | {"cost": m["vtok"] + m.get("anchor_tok", 0),
                                                                     "billed": billed if billed is not None else float("nan")}
    return rows

def boot(d, R, n=10000):
    bs = sorted(sum(R.choice(d) for _ in d) / len(d) for _ in range(n))
    return round(sum(d) / len(d), 3), round(bs[int(.025 * n)], 3), round(bs[int(.975 * n)], 3)

R = random.Random(0); res = {}; ERRS = {}
for run in RUNS:
    for reader in readers_for(run):
        rows = load(run, reader)
        if not rows: continue
        arms = [a for a in "ACMLPED" if any(a in v for v in rows.values())]
        print(f"\n=== {run} · {reader}  (items {len(rows)})")
        tab = {}
        for a in arms:
            v = [x[a] for x in rows.values() if a in x]
            tab[a] = {k: round(sum(e[k] for e in v) / len(v), 3) for k in ("ids", "silent", "abstain", "prose", "cost", "billed")} | {"n": len(v)}
            t = tab[a]; print(f"  {ARM_NAME[a]:28s} ids={t['ids']:.3f} silent={t['silent']:.3f} abstain={t['abstain']:.3f} prose={t['prose']:.3f} cost={t['cost']:.0f} billed={t['billed']:.0f}")
        diffs = {}
        for a, b in [("C", "A"), ("P", "A"), ("C", "P"), ("L", "A"), ("L", "C"), ("M", "A"), ("M", "C"), ("E", "A"), ("E", "C"), ("D", "E"), ("D", "C")]:
            pairs = [x for x in rows.values() if a in x and b in x]
            if len(pairs) < 5: continue
            for k in ("ids", "prose"):
                mu, lo, hi = boot([x[a][k] - x[b][k] for x in pairs], R)
                diffs[f"{a}-{b}:{k}"] = [mu, lo, hi]
                print(f"  {a}-{b} {k:5s}: {mu:+.3f} [{lo:+.3f}, {hi:+.3f}]")
        res[f"{run}|{reader}"] = dict(arms=tab, diffs=diffs)
if ERRS: print("\nfailed reads (arm = dropped refusal/transport error; arm* = unparseable output scored 0):", {f"{r}|{d}": v for (r, d), v in ERRS.items()})
(HERE / ("analysis3.json" if not sys.argv[1:] else f"analysis_{'_'.join(RUNS)}.json")).write_text(json.dumps(res, indent=1))
