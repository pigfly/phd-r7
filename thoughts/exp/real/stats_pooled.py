"""Pooled effects with cluster-bootstrap CIs and Holm-corrected cell counts (review RM-7).
Reader set fixed to the five non-Claude readers. For each family (a set of runs that share items across readers):
  pooled mean difference over (run, reader, item); CI_items = resample items within each run (same draw for every
  reader, i.e. clustered by item; inference conditional on the five readers); CI_both = also resample readers.
  Cell-level tests: per (run, reader) paired bootstrap p-value; counts of significant cells raw and after Holm
  within the family.  usage: python3 stats_pooled.py -> analysis_pooled.json"""
import json, random
from pathlib import Path
from rescore import load
from analyze_ruler import failed_read
from longbench_qa import qa_f1

def load_lb(run):
    """LongBench runs -> {reader: {item: {arm: {"f1": x}}}} (first-line qa_f1, as analyze_longbench.py)."""
    items = {it["item"]: it for it in json.loads((run / "gt.json").read_text())["items"]}
    man = json.loads((run / "manifest.json").read_text()); out = {}
    f = lambda p, it: max(qa_f1((p.get("text") or "").strip().split("\n")[0], g) for g in it["answers"])
    for pf in sorted(run.glob("pred_*.json")):
        rd = pf.stem.replace("pred_or_", "").replace("pred_", ""); pred = json.loads(pf.read_text()); rows = {}
        for m in man:
            p = pred.get(m["name"] + ".png")
            if p is None or failed_read(p) == "drop": continue
            rows.setdefault(m["item"], {})[m["arm"]] = {"f1": 0.0 if failed_read(p) else f(p, items[m["item"]])}
        tf = run / pf.name.replace("pred_", "predtext_")
        if tf.exists():
            for k, p in json.loads(tf.read_text()).items():
                if failed_read(p) == "drop": continue
                rows.setdefault(int(k[2:-4]), {})["T"] = {"f1": 0.0 if failed_read(p) else f(p, items[int(k[2:-4])])}
        out[rd] = rows
    return out

HERE = Path(__file__).parent
READERS = ["gemini-3.5-flash-lite", "gpt-6-luna", "llama-4-maverick", "minimax", "qwen3-vl-235b-a22b-instruct"]
B = 4000

def merged(names):
    """{run: {reader: {item: {arm: m}}}}; runs listed as 'a+b' are merged item-wise (e.g. rbx + rabl2 for arm R)."""
    out = {}
    for n in names:
        parts = n.split("+"); acc = {}
        for p in parts:
            if not (HERE / p / "gt.json").exists(): continue
            for rd, rows in (load_lb if p.startswith("lb") else load)(HERE / p).items():
                for i, arms in rows.items(): acc.setdefault(rd, {}).setdefault(i, {}).update(arms)
        out[parts[0]] = {rd: acc[rd] for rd in READERS if rd in acc}
    return out

def cell_p(d, R):
    m = sum(d) / len(d); bs = [sum(R.choice(d) for _ in d) / len(d) for _ in range(1000)]
    lo = sum(b <= 0 for b in bs) / len(bs); hi = sum(b >= 0 for b in bs) / len(bs)
    return m, min(1.0, 2 * min(lo, hi)) if m != 0 else 1.0

def holm(ps, alpha=0.05):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); sig = [False] * len(ps)
    for k, i in enumerate(order):
        if ps[i] <= alpha / (len(ps) - k): sig[i] = True
        else: break
    return sig

def family(data, a, b, met="recall", R=None):
    R = R or random.Random(0)
    cells = []  # (run, reader, [diffs by item id])
    for run, byr in data.items():
        items = sorted(set.intersection(*[{i for i, r in rows.items() if a in r and b in r} for rows in byr.values()])) if byr else []
        for rd, rows in byr.items(): cells.append((run, rd, {i: rows[i][a][met] - rows[i][b][met] for i in items}))
    cells = [c for c in cells if c[2]]
    if not cells: return None
    pooled = sum(sum(c[2].values()) for c in cells) / sum(len(c[2]) for c in cells)
    runs = sorted({c[0] for c in cells}); its = {r: sorted(next(c[2] for c in cells if c[0] == r)) for r in runs}
    rdset = sorted({c[1] for c in cells})
    def draw(resample_readers):
        # one reader draw shared by every run (readers are crossed with runs), items resampled within each run
        rd = [R.choice(rdset) for _ in rdset] if resample_readers else rdset
        tot = n = 0
        for r in runs:
            byrd = {c[1]: c for c in cells if c[0] == r}
            ii = [R.choice(its[r]) for _ in its[r]]
            for x in rd:
                if x not in byrd: continue
                for i in ii: tot += byrd[x][2][i]; n += 1
        return tot / n
    ci = lambda rr: (lambda s: [round(s[int(.025 * B)], 3), round(s[int(.975 * B)], 3)])(sorted(draw(rr) for _ in range(B)))
    ps = [cell_p(list(c[2].values()), R) for c in cells]
    sig_raw = sum(p < .05 and m > 0 for m, p in ps); neg_raw = sum(p < .05 and m < 0 for m, p in ps)
    hs = holm([p for _, p in ps]); sig_h = sum(h and m > 0 for h, (m, _) in zip(hs, ps)); neg_h = sum(h and m < 0 for h, (m, _) in zip(hs, ps))
    return dict(pooled=round(pooled, 3), ci_items=ci(False), ci_readers_items=ci(True), cells=len(cells),
                sig_pos=sig_raw, sig_neg=neg_raw, sig_pos_holm=sig_h, sig_neg_holm=neg_h)

FAMILIES = {
    "tab1_s5": [f"rbx_s5_{t}+rabl2_s5_{t}" for t in ("single_3", "multikey_1", "multivalue")],
    "tab1_s6": [f"rbx_s6_{t}+rabl2_s6_{t}" for t in ("single_3", "multikey_1", "multivalue")],
    "length": [f"rlong_c{c}k_{t}" for c in (32, 64, 128) for t in ("single_3", "multikey_1", "multivalue")],
    "niq2_s5": ["niq2_s5"], "niq2_s6": ["niq2_s6"], "niq2_s7": ["niq2_s7"], "niq3_s6": ["niq3_s6"],
    "density": [f"rdens_k{k}" for k in (1, 4, 16)],
    "box_s6": [f"rv2_box_s6_{t}" for t in ("single_3", "multikey_1", "multivalue")],
    "s8": [f"rv2_s8_c32k_{t}" for t in ("single_3", "multikey_1")], "s10": [f"rv2_s10_c32k_{t}" for t in ("single_3", "multikey_1")],
    "long_kx": [f"rv2_c{c}k_multikey_1" for c in (64, 128)],
    "longbench": ["lb3_s6_mfqa", "lb3_s6_hotpot"],
}
COMPARE = {"tab1_s5": ["S-A", "S-U", "S-Z", "S-R", "X-K"], "tab1_s6": ["S-A", "S-U", "S-Z", "S-R", "X-K"],
           "length": ["S-A"], "niq2_s5": ["X-K"], "niq2_s6": ["S-A", "X-A", "X-K", "K-A"], "niq2_s7": ["X-K"], "niq3_s6": ["S-A", "X-A", "X-K", "K-A", "X-T"],
           "density": ["S-A", "X-K"], "box_s6": ["B-A", "S-B", "S-A"], "s8": ["S-A", "S-U", "X-K"], "s10": ["S-A", "S-U", "X-K"],
           "long_kx": ["S-A", "X-K", "K-A", "X-A", "X-S"], "longbench": ["S-A", "X-A", "K-A", "X-T"]}

if __name__ == "__main__":
    res = {}
    for fam, runs in FAMILIES.items():
        data = merged(runs)
        if not any(data.values()): continue
        for cmp in COMPARE[fam]:
            a, b = cmp.split("-")
            for met in (("f1",) if fam == "longbench" else ("recall", "f1")):
                r = family(data, a, b, met)
                if r: res[f"{fam}|{cmp}|{met}"] = r; print(f"{fam:9s} {cmp:4s} {met:6s}", r)
    (HERE / "analysis_pooled.json").write_text(json.dumps(res, indent=1))
