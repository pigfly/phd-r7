"""Score reader outputs.  usage: python3 score.py <run_dir> [pred.json ...]
Per arm (or per font size in calibration): id exact-match rate, silent corruption, codename accuracy, vision tokens."""
import json, re, sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

FMT = {"hex12": r"[0-9a-f]{12}", "sha16": r"[0-9a-f]{16}",
       "uuid": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
       "path": r"/var/log/app_[0-9a-f]{4}/run\d\d\.log", "ipport": r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{4,5}", "num6": r"\d{6}"}

def norm(s): return s.strip().strip(".,;()`'\"").lower()

def main():
    run = Path(sys.argv[1]); preds = {}
    for p in sys.argv[2:] or [run / "pred.json"]: preds.update(json.loads(Path(p).read_text()))
    gt = {g["item"]: g for g in json.loads((run / "gt.json").read_text())}
    man = json.loads((run / "manifest.json").read_text())
    agg = defaultdict(lambda: defaultdict(list)); per_kind = defaultdict(lambda: defaultdict(list))
    for m in man:
        key = m["arm"] if "size" not in m else f"size{m['size']}"
        p = preds.get(m["name"]) or preds.get(m["name"] + ".png")
        if p is None: continue
        g = gt[m["item"]]; out = [norm(x) for x in p.get("ids", [])]
        for idd in g["ids"]:
            v, k = idd["value"], idd["kind"]
            ok = v in out
            # silent: not exact, but some emitted string has the right format and is close (plausible-looking wrong id)
            near = [o for o in out if re.fullmatch(FMT[k], o) and SequenceMatcher(None, o, v).ratio() >= 0.6]
            agg[key]["exact"].append(ok); agg[key]["silent"].append((not ok) and bool(near))
            per_kind[key][k].append(ok)
        agg[key]["codename"].append(norm(p.get("codename", "")) == g["codename"])
        agg[key]["vtok"].append(m["vtok"]); agg[key]["chars"].append(len(g["text"])); agg[key]["anc"].append(m.get("anchor_tok", 0))
        if "s_lo" in m: agg[key]["s_lo"].append(m["s_lo"])
    mean = lambda x: sum(x) / len(x) if x else float("nan")
    res = {}
    for key in sorted(agg):
        a = agg[key]
        res[key] = dict(n_imgs=len(a["vtok"]), n_ids=len(a["exact"]), id_exact=round(mean(a["exact"]), 3),
                        silent=round(mean(a["silent"]), 3), codename=round(mean(a["codename"]), 3),
                        vtok=round(mean(a["vtok"]), 1), anchor_tok=round(mean(a["anc"]), 1), chars_per_vtok=round(sum(a["chars"]) / sum(a["vtok"]), 1),
                        by_kind={k: round(mean(v), 2) for k, v in sorted(per_kind[key].items())},
                        **({"mean_s_lo": round(mean(a["s_lo"]), 2)} if a["s_lo"] else {}))
        print(key, json.dumps(res[key]))
    (run / "scores.json").write_text(json.dumps(res, indent=1))

if __name__ == "__main__":
    main()
