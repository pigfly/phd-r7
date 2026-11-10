"""Why does allocation work?  Error anatomy on single-UUID needles (A vs S, five readers) and the entropy x glyph-size study.
(1) format vs content: accuracy on the four hyphens (predictable from the UUID format) vs the 32 hex characters, over answers
    of the right length; (2) fabrication: distribution of wrong hex characters per right-length answer; (3) confusion pairs;
(4) esz: exact-copy recall and character accuracy vs glyph size for English phrases (E), random words (W), random hex (H).
usage: python3 why_analysis.py -> analysis_why.json"""
import json, random
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from analyze_ruler import failed_read, boot

HERE = Path(__file__).parent
R5 = ["gemini-3.5-flash-lite", "gpt-6-luna", "llama-4-maverick", "minimax", "qwen3-vl-235b-a22b-instruct"]
def preds(run, rd):
    f = HERE / run / ("pred_minimax.json" if rd == "minimax" else f"pred_or_{rd}.json")
    return json.loads(f.read_text()) if f.exists() else None

def anatomy(runs):
    st = {a: dict(hy=[0, 0], hex=[0, 0], errs=[], empty=[0, 0], conf=Counter(), conf_partial=Counter(), rd=defaultdict(lambda: [0, 0, 0, 0])) for a in "AS"}
    for run in runs:
        gt = {i["item"]: i for i in json.loads((HERE / run / "gt.json").read_text())["items"]}
        man = json.loads((HERE / run / "manifest.json").read_text())
        for rd in R5:
            pr = preds(run, rd)
            if pr is None: continue
            for m in man:
                if m["arm"] not in "AS": continue
                p = pr.get(m["name"] + ".png")
                if not p or failed_read(p) == "drop": continue
                s = st[m["arm"]]; g = gt[m["item"]]["answers"][0].lower()
                outs = [] if failed_read(p) else [str(x).strip().lower() for x in p.get("ids", []) if str(x).strip()]
                s["empty"][1] += 1; s["empty"][0] += not outs
                cand = [o for o in outs if len(o) == len(g)]
                if not cand: continue
                o = max(cand, key=lambda o: sum(x == y for x, y in zip(o, g)))
                e = 0; pairs = []
                for x, y in zip(o, g):
                    k = "hy" if y == "-" else "hex"; s[k][0] += x == y; s[k][1] += 1
                    if y != "-" and x != y: e += 1; s["conf"][f"{y}>{x}"] += 1; pairs.append(f"{y}>{x}")
                if 1 <= e <= 7: s["conf_partial"].update(pairs)
                s["errs"].append(e); r = s["rd"][rd]; r[0] += 32 - e; r[1] += 32; r[2] += e >= 8; r[3] += 1
    out = {}
    for a, s in st.items():
        n = len(s["errs"]); h = Counter(s["errs"])
        out[a] = dict(n_rightlen=n, n_answers=s["empty"][1], empty=s["empty"][0], hyphen_acc=s["hy"][0] / s["hy"][1], hex_acc=s["hex"][0] / s["hex"][1],
                      exact=h[0] / n, few_1_7=sum(h[k] for k in range(1, 8)) / n, many_8plus=sum(v for k, v in h.items() if k >= 8) / n,
                      median_wrong_if_8plus=sorted(e for e in s["errs"] if e >= 8)[len([e for e in s["errs"] if e >= 8]) // 2] if any(e >= 8 for e in s["errs"]) else None,
                      hist=[h[k] for k in range(33)], top_confusions=s["conf"].most_common(10),
                      top_confusions_partial=s["conf_partial"].most_common(8), n_wrong_partial=sum(s["conf_partial"].values()),
                      per_reader={rd: dict(hex_acc=v[0] / v[1], fabricated=v[2] / v[3], n_rightlen=v[3]) for rd, v in s["rd"].items()})
    return out

def esz(run="esz"):
    gt = {i["item"]: i for i in json.loads((HERE / run / "gt.json").read_text())["items"]}
    man = json.loads((HERE / run / "manifest.json").read_text())
    cell = defaultdict(list); per_reader = defaultdict(list)
    for rd in R5:
        pr = preds(run, rd)
        if pr is None: continue
        for m in man:
            p = pr.get(m["name"] + ".png")
            if not p or failed_read(p) == "drop": continue
            g = gt[m["item"]]["answers"][0].lower()
            outs = [] if failed_read(p) else [str(x).strip().lower() for x in p.get("ids", [])]
            ex = float(any(g in o for o in outs))
            ca = max([SequenceMatcher(None, o, g).ratio() for o in outs] or [0.0])
            cell[(m["type"], m["size"])].append((ex, ca, m["base"], rd)); per_reader[(rd, m["type"], m["size"])].append(ex)
    R = random.Random(0); res = {}
    for (t, s), v in sorted(cell.items()):
        loc = [x for x in v if x[1] >= 0.5]   # the reader found the needle: its answer is at least 50% similar to the gold value
        res[f"{t}|{s}"] = dict(exact=boot([x[0] for x in v], R, 2000), char=sum(x[1] for x in v) / len(v), n=len(v),
                               located=len(loc) / len(v), n_located=len(loc),
                               trans_given_loc=(boot([x[1] for x in loc], R, 2000) if len(loc) >= 5 else None),
                               exact_given_loc=(boot([x[0] for x in loc], R, 2000) if len(loc) >= 5 else None))
    res["per_reader"] = {f"{rd}|{t}|{s}": sum(v) / len(v) for (rd, t, s), v in per_reader.items()}
    pooled = defaultdict(list)
    for (t, s), v in cell.items():
        if s >= 5:
            for x in v:
                if x[1] >= 0.5: pooled[(x[3], t)].append(x[0])
    res["per_reader_found_5to10"] = {f"{rd}|{t}": dict(exact=boot(v, R, 2000) if len(v) >= 5 else None, n=len(v)) for (rd, t), v in pooled.items()}
    return res

if __name__ == "__main__":
    out = {"anatomy": anatomy(["rbx_s5_single_3", "rbx_s6_single_3", "rv2_box_s6_single_3"])}
    if (HERE / "esz" / "manifest.json").exists(): out["esz"] = esz()
    (HERE / "analysis_why.json").write_text(json.dumps(out, indent=1))
    for a, v in out["anatomy"].items():
        print(a, {k: (round(x, 3) if isinstance(x, float) else x) for k, x in v.items() if k not in ("hist", "top_confusions")}, v["top_confusions"][:6])
    if "esz" in out:
        for t in "EWH":
            e = out["esz"]; S = (4, 5, 6, 7, 8, 10)
            print(t, "located", [round(e[f"{t}|{s}"]["located"], 2) for s in S],
                  "trans|loc", [e[f"{t}|{s}"]["trans_given_loc"] for s in S], "exact|loc", [e[f"{t}|{s}"]["exact_given_loc"] for s in S])
