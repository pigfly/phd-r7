"""Analysis of the selection-method control (sel_control.py).
Arms: A typical COC, S current detector (both from niq3_s6), P simple rule, Q LM surprisal (niq3sel_s6).
Reports per-reader and five-reader mean recall, tokens per task, paired differences with a bootstrap over
readers and items (as in stats_pooled.py), and recall split by whether the selector enlarged the target.
usage: python3 sel_analyze.py -> analysis_selection.json"""
import json, random, statistics as st
from pathlib import Path
from rescore import load

HERE = Path(__file__).parent
READERS = ["gemini-3.5-flash-lite", "gpt-6-luna", "llama-4-maverick", "qwen3-vl-235b-a22b-instruct", "minimax"]
ARMS = "ASPQ"

def boot(data, a, b, B=2000, seed=0):
    """pooled paired difference b-a: mean over readers of mean over items; bootstrap readers and items"""
    R = random.Random(seed)
    def est(rs, its):
        return st.mean(st.mean(data[r][i][b] - data[r][i][a] for i in its[r]) for r in rs)
    its = {r: [i for i in data[r] if a in data[r][i] and b in data[r][i]] for r in data}
    rs = list(data); point = est(rs, its); bs = []
    for _ in range(B):
        rr = [R.choice(rs) for _ in rs]
        ii = {r: [R.choice(its[r]) for _ in its[r]] for r in set(rr)}
        bs.append(est(rr, ii))
    bs.sort(); return round(point, 3), round(bs[int(.025 * B)], 3), round(bs[int(.975 * B)], 3)

def main():
    a = load(HERE / "niq3_s6"); b = load(HERE / "niq3sel_s6")
    man = json.loads((HERE / "niq3sel_s6" / "manifest.json").read_text())
    man0 = json.loads((HERE / "niq3_s6" / "manifest.json").read_text())
    gt = {it["item"]: it for it in json.loads((HERE / "niq3_s6" / "gt.json").read_text())["items"]}
    sel = {(m["item"], m["arm"]): m["target_selected"] for m in man}
    for it in gt.values(): sel[(it["item"], "S")] = bool(it.get("flagged")); sel[(it["item"], "A")] = False
    rec, tok = {}, {}
    for r in READERS:
        rec[r], tok[r] = {}, {}
        for i in gt:
            row = {**{k: v for k, v in a.get(r, {}).get(i, {}).items() if k in "AS"}, **{k: v for k, v in b.get(r, {}).get(i, {}).items() if k in "PQ"}}
            if all(k in row for k in ARMS):
                rec[r][i] = {k: row[k]["recall"] for k in ARMS}; tok[r][i] = {k: row[k]["billed"] for k in ARMS}
    out = {"n_items": {r: len(rec[r]) for r in READERS}}
    out["recall_per_reader"] = {r: {k: round(st.mean(v[k] for v in rec[r].values()), 3) for k in ARMS} for r in READERS if rec[r]}
    out["recall_mean"] = {k: round(st.mean(out["recall_per_reader"][r][k] for r in out["recall_per_reader"]), 3) for k in ARMS}
    tr = [r for r in READERS if r != "minimax" and tok[r]]
    out["tokens_mean"] = {k: round(st.mean(st.mean(v[k] for v in tok[r].values()) for r in tr)) for k in ARMS}
    out["vtok_mean"] = {k: round(st.mean(m["vtok"] for m in (man if k in "PQ" else man0) if m["arm"] == k)) for k in ARMS}
    out["sel_chars_mean"] = {k: round(st.mean(m["sel_chars"] for m in man if m["arm"] == k)) for k in "PQ"}
    out["targets_selected"] = {k: sum(sel[(i, k)] for i in gt) for k in ARMS}
    data = {r: rec[r] for r in READERS if rec[r]}
    out["diff_vs_A"] = {k: boot(data, "A", k) for k in "SPQ"}
    out["diff_Q_vs_S"] = boot(data, "S", "Q"); out["diff_Q_vs_P"] = boot(data, "P", "Q"); out["diff_P_vs_S"] = boot(data, "S", "P")
    split = {}
    for k in "SPQ":
        on = [v[k] for r in data for i, v in data[r].items() if sel[(i, k)]]; on_a = [v["A"] for r in data for i, v in data[r].items() if sel[(i, k)]]
        off = [v[k] for r in data for i, v in data[r].items() if not sel[(i, k)]]; off_a = [v["A"] for r in data for i, v in data[r].items() if not sel[(i, k)]]
        split[k] = dict(selected=dict(n=len(on) // max(len(data), 1), arm=round(st.mean(on), 3) if on else None, coc=round(st.mean(on_a), 3) if on else None),
                        not_selected=dict(n=len(off) // max(len(data), 1), arm=round(st.mean(off), 3) if off else None, coc=round(st.mean(off_a), 3) if off else None))
    out["split_by_target_selected"] = split
    for k in "PQ":
        for name, want in (("selected", True), ("not_selected", False)):
            sub = {r: {i: v for i, v in data[r].items() if sel[(i, k)] == want} for r in data}
            out["split_by_target_selected"][k][name]["diff_vs_A"] = boot(sub, "A", k)
    (HERE / "analysis_selection.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))

if __name__ == "__main__":
    main()
