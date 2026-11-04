"""Score E3 LongBench QA runs (lb_*): LongBench qa_f1_score (max over gold answers) for T text-only, A uniform, M.
usage: python3 analyze_longbench.py  -> prints tables, writes analysis_longbench.json"""
import json, random
from collections import defaultdict
from pathlib import Path
from analyze_ruler import failed_read, boot
from longbench_qa import qa_f1

HERE = Path(__file__).parent
R = random.Random(0); res = {}; fails = defaultdict(list)

def f1(p, it):
    t = (p.get("text") or "").strip().split("\n")[0]  # LongBench scores the first line for these QA tasks
    return max(qa_f1(t, g) for g in it["answers"])

for run in sorted(HERE.glob("lb*_*")):
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
            if fr: fails[f"{run.name}|{reader}"].append(m["arm"] + ("" if fr == "drop" else "*"))
            if fr == "drop": continue
            rows[m["item"]][m["arm"]] = {"f1": 0.0 if fr else f1(p, items[m["item"]]), "billed": p.get("usage", {}).get("prompt_tokens", 0)}
        tf = run / pf.name.replace("pred_", "predtext_")
        if tf.exists():
            for k, p in json.loads(tf.read_text()).items():
                fr = failed_read(p)
                if fr == "drop": continue
                rows[int(k[2:-4])]["T"] = {"f1": 0.0 if fr else f1(p, items[int(k[2:-4])]), "billed": p.get("usage", {}).get("prompt_tokens", 0)}
        tab = {a: {k: round(sum(r[a][k] for r in rows.values() if a in r) / max(1, sum(a in r for r in rows.values())), 3)
                   for k in ("f1", "billed")} for a in "TAMSLKX"}
        diffs = {}
        for a, b in (("M", "A"), ("A", "T"), ("M", "T"), ("S", "A"), ("L", "A"), ("L", "M"), ("K", "A"), ("X", "A"), ("X", "K"), ("S", "T"), ("X", "T"), ("K", "T")):
            pr = [r for r in rows.values() if a in r and b in r]
            if len(pr) >= 5: diffs[f"{a}-{b}"] = boot([r[a]["f1"] - r[b]["f1"] for r in pr], R)
        res[f"{run.name}|{reader}"] = dict(arms=tab, diffs=diffs, n=len(rows))
        fmt = lambda k: ("%+.3f [%+.3f,%+.3f]" % tuple(diffs[k])) if k in diffs else "-"
        print(f"{run.name:14s} {reader:28s} " + " ".join(f"{a}={tab[a]['f1']:.3f}" for a in "TAMSLKX" if tab[a]["billed"] or tab[a]["f1"])
              + "".join(f"  {k} {fmt(k)}" for k in ("M-A", "S-A", "L-A", "K-A", "X-A", "A-T", "X-T") if k in diffs))
if fails: print("failed reads (arm = dropped; arm* = scored 0):", dict(fails))
(HERE / "analysis_longbench.json").write_text(json.dumps(res, indent=1))
