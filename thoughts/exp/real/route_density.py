"""Density-aware routing on the hazard-density sweep (rdens_k*), offline from existing reads.
Feature (known before any model call): r = estimated anchor tokens / vision tokens of the S image.
Policy R(tau): r <= tau -> X (S image + anchors), else -> T (plain text). tau is picked on one half of the items
(maximise recall - LAMBDA * cost/text_cost) and evaluated on the other half (2-fold), per reader.
Compared with fixed policies T / A / S / K / X. Cost = provider-billed prompt tokens.
usage: python3 route_density.py  -> prints table, writes analysis_routing.json"""
import json, statistics as St
from pathlib import Path
from analyze_ruler import score, failed_read

HERE = Path(__file__).parent
READERS = ["gemini-3.5-flash-lite", "gpt-6-luna", "llama-4-maverick", "qwen3-vl-235b-a22b-instruct"]
TAUS = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0, 1e9]
LAMBDA = 0.5  # recall points traded per full text cost

def rows_for(reader):
    out = []
    for run in sorted(HERE.glob("rdens_k*")):
        gt = json.loads((run / "gt.json").read_text()); items = {it["item"]: it for it in gt["items"]}
        man = json.loads((run / "manifest.json").read_text())
        pred = json.loads((run / f"pred_or_{reader}.json").read_text())
        text = json.loads((run / f"predtext_or_{reader}.json").read_text())
        per = {}
        for m in man:
            p = pred.get(m["name"] + ".png")
            if p is None or failed_read(p) == "drop": continue
            rec = 0.0 if failed_read(p) else score(p, items[m["item"]])["recall"]
            per.setdefault(m["item"], {})[m["arm"]] = (rec, p.get("usage", {}).get("prompt_tokens", 0), m)
        for i, d in per.items():
            p = text.get(f"T_{i}.png")
            if p is None or failed_read(p) == "drop" or not all(a in d for a in "ASKX"): continue
            rec = 0.0 if failed_read(p) else score(p, items[i])["recall"]
            d["T"] = (rec, p.get("usage", {}).get("prompt_tokens", 0), None)
            r = d["X"][2]["anchor_tok"] / d["S"][2]["vtok"]
            out.append(dict(k=int(run.name.split("_k")[1]), item=i, r=r, **{a: d[a][:2] for a in "TASKX"}))
    return out

def route(row, tau): return row["X"] if row["r"] <= tau else row["T"]
def evaluate(rows, pick):
    rec = St.mean(pick(r)[0] for r in rows); cost = St.mean(pick(r)[1] for r in rows)
    return rec, cost, cost / St.mean(r["T"][1] for r in rows)
def utility(rows, tau):
    rec, _, rel = evaluate(rows, lambda r: route(r, tau)); return rec - LAMBDA * rel

res = {}
print(f"{'reader':28s} {'policy':10s} {'recall':>7s} {'cost':>7s} {'cost/T':>7s}")
for reader in READERS:
    rows = rows_for(reader); folds = [[r for r in rows if r["item"] % 2 == f] for f in (0, 1)]
    routed, taus = [], []
    for f in (0, 1):
        tau = max(TAUS, key=lambda t: utility(folds[1 - f], t)); taus.append(tau)
        routed += [route(r, tau) for r in folds[f]]
    pol = {a: evaluate(rows, lambda r, a=a: r[a]) for a in "TASKX"}
    rr, rc = St.mean(x[0] for x in routed), St.mean(x[1] for x in routed)
    pol["route"] = (rr, rc, rc / St.mean(r["T"][1] for r in rows))
    res[reader] = dict(policies={k: [round(x, 3) for x in v] for k, v in pol.items()}, taus=taus, n=len(rows))
    for k, (rec, cost, rel) in pol.items():
        print(f"{reader:28s} {k:10s} {rec:7.3f} {cost:7.0f} {rel:7.2f}" + (f"   tau={taus}" if k == "route" else ""))
    print()
agg = {k: [St.mean(res[r]["policies"][k][j] for r in READERS) for j in range(3)] for k in ["T", "A", "S", "K", "X", "route"]}
print("MEAN over readers:"); [print(f"  {k:6s} recall {v[0]:.3f}  cost {v[1]:6.0f}  cost/T {v[2]:.2f}") for k, v in agg.items()]
print("\nby density k (mean over readers): recall / cost-per-T of route vs X vs T")
for k in sorted({r["k"] for r in rows_for(READERS[0])}):
    line = []
    for reader in READERS:
        rows = [r for r in rows_for(reader) if r["k"] == k]; tau = St.median(res[reader]["taus"])
        line.append((evaluate(rows, lambda r: route(r, tau)), evaluate(rows, lambda r: r["X"]), evaluate(rows, lambda r: r["T"]),
                     St.mean(r["r"] for r in rows)))
    m = lambda j, q: St.mean(x[j][q] for x in line)
    print(f"  k={k:3d}  r={St.mean(x[3] for x in line):5.2f}  route {m(0,0):.2f}/{m(0,2):.2f}  X {m(1,0):.2f}/{m(1,2):.2f}  T {m(2,0):.2f}/1.00")
(HERE / "analysis_routing.json").write_text(json.dumps(dict(per_reader=res, mean=agg, lam=LAMBDA), indent=1))

# ---- frontier: route-X (ours) vs route-K (R-or-R style: anchors on the uniform image, else text), sweeping tau ----
def route_k(row, tau): return row["K"] if row["r"] <= tau else row["T"]
print("\nFRONTIER (mean over readers): tau -> recall / cost-per-T   [route-X | route-K]")
frontier = []
for tau in TAUS:
    vx = [evaluate(rows_for(rd), lambda r: route(r, tau)) for rd in READERS]
    vk = [evaluate(rows_for(rd), lambda r: route_k(r, tau)) for rd in READERS]
    fx = (St.mean(v[0] for v in vx), St.mean(v[2] for v in vx)); fk = (St.mean(v[0] for v in vk), St.mean(v[2] for v in vk))
    frontier.append(dict(tau=tau, X=fx, K=fk))
    print(f"  tau={tau:>6g}   X {fx[0]:.3f} / {fx[1]:.3f}   |   K {fk[0]:.3f} / {fk[1]:.3f}")
sparse = {}
for arm in "XKT":
    v = [evaluate([r for r in rows_for(rd) if r["k"] <= 16], lambda r, a=arm: r[a]) for rd in READERS]
    sparse[arm] = (St.mean(x[0] for x in v), St.mean(x[2] for x in v))
print("\nsparse/mid regime only (k <= 16): " + "  ".join(f"{a} recall {v[0]:.3f} cost/T {v[1]:.3f}" for a, v in sparse.items()))
j = json.loads((HERE / "analysis_routing.json").read_text()); j["frontier"] = frontier; j["sparse_k_le_16"] = sparse
(HERE / "analysis_routing.json").write_text(json.dumps(j, indent=1))
