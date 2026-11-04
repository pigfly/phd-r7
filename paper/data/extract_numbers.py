"""Collect every number the paper reports from thoughts/exp/real/analysis_* into paper/data/numbers.json,
and write a human-readable registry (numbers_registry.md) with the source file of each block.
usage: python3 paper/data/extract_numbers.py"""
import json, statistics as St
from pathlib import Path

EXP = Path(__file__).resolve().parents[2] / "thoughts" / "exp" / "real"
OUT = Path(__file__).resolve().parent
READERS = ["claude-sonnet-5.5", "gemini-3.5-flash-lite", "gpt-6-luna", "qwen3-vl-235b-a22b-instruct",
           "llama-4-maverick", "minimax"]
NAME = {"claude-sonnet-5.5": "Claude Sonnet 5.5", "gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite",
        "gpt-6-luna": "GPT-6 Luna", "qwen3-vl-235b-a22b-instruct": "Qwen3-VL-235B",
        "llama-4-maverick": "Llama 4 Maverick", "minimax": "MiniMax-M3"}
r = json.loads((EXP / "analysis_ruler.json").read_text())
lb = json.loads((EXP / "analysis_longbench.json").read_text())
num, reg = {}, []

def mean(xs): xs = [x for x in xs if x is not None]; return round(St.mean(xs), 6) if xs else None  # round once, at display time

# --- Table 1: equal-budget arms on RULER 16K. rbx_* = rbase_* (A,S,U,Z,K) merged item-by-item with rabl_* (R,X) ---
ARMS1 = "ASUZKRX"
def has(c, a): return bool(c["arms"][a]["recall"] or c["arms"][a]["billed"] or c["arms"][a]["vtok"])
t1 = {}
for d in ("s5", "s6"):
    for rd in READERS:
        cells = [r[k] for k in r if k.startswith(f"rbx_{d}_") and k.endswith("|" + rd)]
        t1[f"{d}|{rd}"] = {a: (mean(c["arms"][a]["recall"] for c in cells) if any(has(c, a) for c in cells) else None) for a in ARMS1} | \
            {f"billed_{a}": mean(c["arms"][a]["billed"] or None for c in cells) for a in ARMS1} | \
            {f"silent_{a}": mean(c["arms"][a]["silent"] for c in cells) for a in "ASUZK"} | \
            {"sig_S-A": sum(c["diffs"]["S-A"][1] > 0 for c in cells), "n_cells": len(cells)}
    allc = [r[k] for k in r if k.startswith(f"rbx_{d}_")]
    t1[f"{d}|mean"] = {a: mean(c["arms"][a]["recall"] for c in allc if has(c, a)) for a in ARMS1} | \
        {f"billed_{a}": mean(c["arms"][a]["billed"] or None for c in allc) for a in ARMS1} | \
        {f"silent_{a}": mean(c["arms"][a]["silent"] for c in allc) for a in "ASUZK"}
    for b in "UZKR":
        x = [c["diffs"][f"S-{b}"] for c in allc if f"S-{b}" in c["diffs"]]
        t1[f"{d}|S-{b}"] = dict(mean=mean(y[0] for y in x), sig_better=sum(y[1] > 0 for y in x), sig_worse=sum(y[2] < 0 for y in x), n=len(x))
    for dd in ("X-K", "X-A", "R-A"):
        x = [c["diffs"][dd] for c in allc if dd in c["diffs"]]
        t1[f"{d}|{dd}"] = dict(mean=mean(y[0] for y in x), sig_better=sum(y[1] > 0 for y in x), sig_worse=sum(y[2] < 0 for y in x), n=len(x))
num["table1_baselines_ruler16k"] = t1
reg.append("table1_baselines_ruler16k <- analysis_ruler.json keys rbx_s{5,6}_*|<reader> (rbase A/S/U/Z/K + rabl R/X on identical items; 16K chars, N=25/task, 3 tasks; R/X not run for Claude)")

# --- Length scaling (rlong) ---
ls = {}
for L in ("32k", "64k", "128k"):
    for rd in READERS:
        cells = [r[k] for k in r if k.startswith(f"rlong_c{L}_") and k.endswith("|" + rd)]
        ls[f"{L}|{rd}"] = {a: mean(c["arms"][a]["recall"] for c in cells) for a in "AS"} | \
            {f"billed_{a}": mean(c["arms"][a]["billed"] or None for c in cells) for a in "AST"} | {"T": mean(c["arms"]["T"]["recall"] for c in cells if c["arms"]["T"]["billed"] or c["arms"]["T"]["recall"])}
    allc = [r[k] for k in r if k.startswith(f"rlong_c{L}_")]
    d = [c["diffs"]["S-A"] for c in allc]
    ls[f"{L}|mean"] = {a: mean(c["arms"][a]["recall"] for c in allc) for a in "AS"} | \
        {f"billed_{a}": mean(c["arms"][a]["billed"] or None for c in allc) for a in "AST"} | \
        {"S-A": mean(y[0] for y in d), "sig": sum(y[1] > 0 for y in d), "n": len(d)}
num["length_scaling"] = ls
reg.append("length_scaling <- analysis_ruler.json keys rlong_c{32,64,128}k_*|<reader> (6px, N=20/task)")

# --- Density sweep ---
den = {}
for kk in (1, 4, 16, 64, 128, 256):
    cells = {k.split("|")[1]: v for k, v in r.items() if k.startswith(f"rdens_k{kk}|") and k.split("|")[1] in READERS}
    den[str(kk)] = {a: mean(v["arms"][a]["recall"] for v in cells.values()) for a in "ASKX"} | \
        {f"billed_{a}": mean(v["arms"][a]["billed"] or None for v in cells.values()) for a in "ASKX"} | \
        {"per_reader": {rd: {a: v["arms"][a]["recall"] for a in "ASKX"} for rd, v in cells.items()}}
num["density_sweep"] = den
num["routing"] = json.loads((EXP / "analysis_routing.json").read_text())
reg.append("density_sweep <- analysis_ruler.json rdens_k*|<reader> (32K, N=25); routing <- analysis_routing.json")

# --- LongBench holdout with anchors (lb3) + M/S/L (lb2) ---
num["longbench_lb3"] = {k: v for k, v in lb.items() if k.startswith("lb3_")}
num["longbench_lb2"] = {k: v for k, v in lb.items() if k.startswith("lb2_")}
num["longbench_lb_text"] = {k: v for k, v in lb.items() if k.startswith("lb_s6")}
reg.append("longbench_lb3 (A/S/K/X, N=50/task) / lb2 (A/M/S/L) / lb_s6 (T/A/M, disjoint samples) <- analysis_longbench.json")

# --- Detector ablation ---
det = {}
for run in ("rdet_mv7", "rdet_mv4"):
    c = {k.split("|")[1]: v for k, v in r.items() if k.startswith(run + "|")}
    det[run] = {a: mean(v["arms"][a]["recall"] for v in c.values()) for a in "ASOXY"} | \
        {f"billed_{a}": mean(v["arms"][a]["billed"] or None for v in c.values()) for a in "ASOXY"} | \
        {"per_reader": {rd: {a: v["arms"][a]["recall"] for a in "ASOXY"} for rd, v in c.items()}}
num["detector_ablation"] = det
reg.append("detector_ablation <- analysis_ruler.json rdet_mv{7,4}|<reader> (16K, N=25, 5 readers)")

niq = {k.split("|")[1]: v for k, v in r.items() if k.startswith("niq2_s6|")}
num["niq"] = {rd: {"arms": {a: v["arms"][a] for a in "TASKX"}, "diffs": v["diffs"]} for rd, v in niq.items()}
reg.append("niq <- analysis_ruler.json niq2_s6|<reader> (natural identifiers from LongBench docs, N=60, 6px; niq_s6 discarded: glued-token artifacts)")
num["real_density"] = json.loads((EXP / "analysis_real_density.json").read_text())
num["claude_subagent"] = json.loads((EXP / "analysis_claude_reader.json").read_text())
num["sweep_short"] = json.loads((EXP / "analysis_sw_s5_sw_s6_sw_s8_sw_s10.json").read_text())
num["mlocal"] = (EXP / "analysis_mlocal.txt").read_text()
reg += ["real_density <- analysis_real_density.json", "claude_subagent <- analysis_claude_reader.json",
        "sweep_short (E2 phase diagram, short synthetic) <- analysis_sw_s5_sw_s6_sw_s8_sw_s10.json"]

# --- Stage-4 revision (review round 1): precision-aware rescoring, pooled effects, new controls ---
rs = json.loads((EXP / "analysis_rescore.json").read_text())
num["rescore"] = rs
num["pooled"] = json.loads((EXP / "analysis_pooled.json").read_text())
R5 = [x for x in READERS if x != "claude-sonnet-5.5"]
def m5(run, arm, key):
    v = [rs[f"{run}|{rd}"]["arms"][arm][key] for rd in R5 if f"{run}|{rd}" in rs and arm in rs[f"{run}|{rd}"]["arms"]]
    return mean(v)
def b5(run, arm):
    v = [rs[f"{run}|{rd}"]["arms"][arm]["billed"] or None for rd in R5 if f"{run}|{rd}" in rs and arm in rs[f"{run}|{rd}"]["arms"]]
    return mean(v)
rev = {}
for run, arms in [("niq2_s5", "ASKX"), ("niq2_s6", "ASKXT"), ("niq2_s7", "ASKX"), ("niq3_s6", "ASKXT"),
                  *[(f"rv2_box_s6_{t}", "ABS") for t in ("single_3", "multikey_1", "multivalue")],
                  *[(f"rv2_s{z}_c32k_{t}", "ASUKX") for z in (8, 10) for t in ("single_3", "multikey_1")],
                  *[(f"rv2_c{c}k_multikey_1", "ASKX") for c in (64, 128)],
                  *[(f"rbx_s{z}_{t}", "ASUZKX") for z in (5, 6) for t in ("single_3", "multikey_1", "multivalue")]]:
    rev[run] = {a: {k: m5(run, a, k) for k in ("recall", "f1", "exact", "nret")} | {"billed": b5(run, a)} for a in arms}
    if "K" in arms: rev[run]["pick_K"] = m5(run, "K", "pick"); rev[run]["gin_K"] = m5(run, "K", "gin"); rev[run]["nanc_K"] = m5(run, "K", "nanc")
num["revision_5readers"] = rev
num["niq3_flagged"] = sum(it.get("flagged", 0) for it in json.loads((EXP / "niq3_s6" / "gt.json").read_text())["items"])
reg.append("rescore / revision_5readers <- analysis_rescore.json (precision-aware F1, exact-set, #returned, copy baselines; 5 non-Claude readers)")
reg.append("pooled <- analysis_pooled.json (item-cluster and reader+item bootstrap CIs; Holm within family; 5 readers)")
num["reader_names"] = NAME
(OUT / "numbers.json").write_text(json.dumps(num, indent=1))
(OUT / "numbers_registry.md").write_text("# Number registry (all paper numbers come from these files)\n\n" + "\n".join("- " + x for x in reg) + "\n")
print(json.dumps({k: num["table1_baselines_ruler16k"][k] for k in ("s5|mean", "s6|mean", "s5|S-U", "s6|S-K")}, indent=0))
print(json.dumps({k: v for k, v in num["length_scaling"].items() if k.endswith("mean")}, indent=0))
