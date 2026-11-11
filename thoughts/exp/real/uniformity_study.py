"""Recall vs entropy uniformity across all equal-budget arms (Andy feedback, 2026-11-11).
For every image: per-character residual entropy h_i (entropy_map.surprisal) and glyph area a_i (vision tokens), loads of
n-character reading-order windows l = sum h / sum a, mean load lam = sum h / sum a over the document, and
  U_max  = lam / max l           U_tail = lam / mean of the top 1% of window loads
Per needle: load of the window centred on the needle (absolute bits per vision token) and whether each reader recalled it.
usage: python3 uniformity_study.py  -> analysis_uniformity.json"""
import json, random, re
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
import entropy_map as E, make_items as M
from stats_pooled import merged, READERS

HERE = Path(__file__).parent
NS = (16, 32, 48, 64); N0 = 48
GROUPS = {  # name: (runs, arms, size)
    **{f"tab1_s{s}_{t}": ([f"rbx_s{s}_{t}+rabl2_s{s}_{t}"], "AUZRS", s) for s in (5, 6) for t in ("single_3", "multikey_1", "multivalue")},
    **{f"half_s{s}_{t}": ([f"rhalf_s{s}_{t}"], "H", s) for s in (5, 6) for t in ("multikey_1", "multivalue")},
    **{f"box_s6_{t}": ([f"rv2_box_s6_{t}"], "ABS", 6) for t in ("single_3", "multikey_1", "multivalue")},
    **{f"s{s}_{t}": ([f"rv2_s{s}_c32k_{t}"], "AUS", s) for s in (8, 10) for t in ("single_3", "multikey_1")},
    "niq2_s6": (["niq2_s6"], "AS", 6), "niq3_s6": (["niq3_s6"], "AS", 6),
    **{f"len{c}k_{t}": ([f"rlong_c{c}k_{t}"], "AS", 6) for c in (32, 64, 128) for t in ("single_3", "multikey_1", "multivalue")},
}

def image_stats(run, m, it, size, seed_cache):
    arm = m["arm"]; M.STRICT = arm in ("S", "X", "B", "H"); M.ORACLE = None
    try:
        if arm == "R":
            if run not in seed_cache: seed_cache[run] = E.find_seed(run, json.loads((run / "gt.json").read_text())["items"])
            sd, golds = seed_cache[run]; gi = dict(it); gi["gold"] = golds[m["item"]]; M.ORACLE = E.r_pick(gi, sd)
        if arm == "H": M.ORACLE = set(m["enlarged"])
        h, a = E.char_load(it["text"], arm, m, size)
    finally:
        M.STRICT = False; M.ORACLE = None
    lam = h.sum() / a.sum(); r = dict(lam=float(lam))
    for n in NS:
        w = E.window_load(h, a, n); top = np.sort(w)[-max(1, len(w) // 100):]
        r[f"Umax{n}"] = float(lam / w.max()); r[f"Utail{n}"] = float(lam / top.mean())
        r[f"Utop{n}"] = float(lam / np.sort(w)[-160:].mean())  # fixed number of windows (= 1% of a 16K document)
    w = E.window_load(h, a, N0); needles = {}
    for v in it["answers"]:
        ph = re.search(r'immediately after the words "(.*?)"\?', it["prompt"])
        k = (it["text"].find(ph.group(1)) + len(ph.group(1)) + 1) if ph else it["text"].find(v)
        if k < 0: continue
        c = min(max(0, k + len(v) // 2 - N0 // 2), len(w) - 1); needles[v] = float(w[c])
    r["needle_load"] = needles
    return r

def main():
    out = {}; seed_cache = {}
    for gname, (runs, arms, size) in GROUPS.items():
        data = merged(runs); run = HERE / runs[0].split("+")[0]
        if not (run / "gt.json").exists() or not data.get(run.name): print("skip", gname); continue
        g = json.loads((run / "gt.json").read_text()); items = {it["item"]: it for it in g["items"]}
        parts = runs[0].split("+")
        man = [m | {"_part": p} for p in parts for m in json.loads((HERE / p / "manifest.json").read_text()) if m["arm"] in arms]
        preds = {p: {rd: json.loads(f.read_text()) for rd in READERS for f in [HERE / p / ("pred_minimax.json" if rd == "minimax" else f"pred_or_{rd}.json")] if f.exists()} for p in parts}
        cache = HERE / runs[0].split("+")[0] / "uniformity.json"
        old = json.loads(cache.read_text()) if cache.exists() else {}
        rows = []
        for m in man:
            key = f"{m['arm']}|{m['item']}"
            if key not in old or "Utop48" not in old[key]: old[key] = image_stats(HERE / m["_part"], m, items[m["item"]], size, seed_cache)
            st = old[key]
            rec = {rd: data[run.name][rd][m["item"]][m["arm"]]["recall"] for rd in data[run.name]
                   if m["item"] in data[run.name][rd] and m["arm"] in data[run.name][rd][m["item"]]}
            # per-needle hits per reader
            hits = {}
            for rd in rec:
                pr = preds[m["_part"]].get(rd, {}).get(m["name"] + ".png") or {}
                outs = [str(x).strip().strip(".,;()`'\"").lower() for x in pr.get("ids", [])]
                hits[rd] = {v: any(v.lower() in o for o in outs) for v in items[m["item"]]["answers"]}
            rows.append(dict(arm=m["arm"], item=m["item"], recall=rec, hits=hits, **st))
        cache.write_text(json.dumps(old))
        out[gname] = rows
        by = defaultdict(list)
        for r in rows: by[r["arm"]].append(r)
        print(gname, {a: (round(np.mean([x[f"Utail{N0}"] for x in v]), 3), round(np.mean([np.mean(list(x["recall"].values())) for x in v if x["recall"]]), 2)) for a, v in by.items()})
    (HERE / "analysis_uniformity_raw.json").write_text(json.dumps(out))

if __name__ == "__main__":
    main()
