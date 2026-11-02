"""Score RULER NIAH runs (ruler_*): RULER string_match_all recall (fraction of gold values present, case-insensitive)
+ silent corruption (an output of the right length that is >=60% similar to a gold value but not equal).
usage: python3 analyze_ruler.py  -> prints tables, writes analysis_ruler.json"""
import json, random
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).parent
ARMS = "ACM"

EXC = ("URLError", "HTTPError", "TimeoutError", "Remote", "IncompleteRead", "ConnectionReset", "JSONDecodeError", "KeyError")
def failed_read(p):
    """None = usable; 'drop' = refusal / empty / transport error (excluded); 'zero' = reader produced unparseable
    output, e.g. degenerate repetition up to max_tokens (scored as an empty answer)."""
    if "error" not in p: return None
    e = (p["error"] or "").strip()
    return "drop" if not e or e.startswith(EXC) else "zero"

def score(p, it):
    out = [str(x).strip().strip(".,;()`'\"").lower() for x in p.get("ids", [])]
    rec = sil = 0
    for v in it["answers"]:
        ok = v.lower() in out or any(v.lower() in o for o in out); rec += ok
        sil += (not ok) and any(len(o) == len(v) and SequenceMatcher(None, o, v.lower()).ratio() >= 0.6 for o in out)
    return dict(recall=rec / len(it["answers"]), silent=sil / len(it["answers"]))

def boot(d, R, n=10000):
    bs = sorted(sum(R.choice(d) for _ in d) / len(d) for _ in range(n))
    return [round(sum(d) / len(d), 3), round(bs[int(.025 * n)], 3), round(bs[int(.975 * n)], 3)]

R = random.Random(0); res = {}; drops = defaultdict(list)
for run in sorted(HERE.glob("ruler_s*")):
    if not (run / "gt.json").exists(): continue
    gt = json.loads((run / "gt.json").read_text()); items = {it["item"]: it for it in gt["items"]}
    man = json.loads((run / "manifest.json").read_text())
    for pf in sorted(run.glob("pred_*.json")):
        reader = pf.stem.replace("pred_or_", "").replace("pred_", ""); pred = json.loads(pf.read_text())
        rows = defaultdict(dict)
        for m in man:
            p = pred.get(m["name"] + ".png")
            if p is None: continue
            fr = failed_read(p)
            if fr: drops[f"{run.name}|{reader}"].append(m["arm"] + ("" if fr == "drop" else "*"))
            if fr == "drop": continue
            if fr == "zero": p = {"ids": [], "usage": p.get("usage", {})}
            rows[m["item"]][m["arm"]] = score(p, items[m["item"]]) | {"vtok": m["vtok"], "billed": p.get("usage", {}).get("prompt_tokens", 0)}
        tab = {a: {k: round(sum(r[a][k] for r in rows.values() if a in r) / max(1, sum(a in r for r in rows.values())), 3)
                   for k in ("recall", "silent", "vtok", "billed")} for a in ARMS}
        diffs = {}
        for a, b in (("M", "A"), ("C", "A"), ("M", "C")):
            pr = [r for r in rows.values() if a in r and b in r]
            if len(pr) >= 5: diffs[f"{a}-{b}"] = boot([r[a]["recall"] - r[b]["recall"] for r in pr], R)
        res[f"{run.name}|{reader}"] = dict(arms=tab, diffs=diffs, n=len(rows))
        print(f"{run.name:22s} {reader:28s} " + " ".join(f"{a}={tab[a]['recall']:.2f}/{tab[a]['silent']:.2f}/{tab[a]['billed']:.0f}" for a in ARMS)
              + "  M-A " + ("%+.2f [%+.2f,%+.2f]" % tuple(diffs["M-A"]) if "M-A" in diffs else "-"))
if drops: print("failed reads (arm = dropped refusal/transport error; arm* = unparseable output scored 0):", dict(drops))
(HERE / "analysis_ruler.json").write_text(json.dumps(res, indent=1))
