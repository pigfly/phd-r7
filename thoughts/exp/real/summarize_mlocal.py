"""Summary of the M-local round: LongBench holdout (lb2_*) harm and RULER (ruler2_*) retention for arms M / S / L.
usage: python3 analyze_longbench.py; python3 analyze_ruler.py; python3 summarize_mlocal.py"""
import json, statistics as S
lb = {k: v for k, v in json.load(open("analysis_longbench.json")).items() if k.startswith("lb2_")}
ru = {k: v for k, v in json.load(open("analysis_ruler.json")).items() if k.startswith("ruler2_")}
print(f"LongBench holdout ({len(lb)} reader x task cells), qa_f1 difference vs A:")
for arm in "MSL":
    d = [v["diffs"][f"{arm}-A"] for v in lb.values()]
    print(f"  {arm}-A  mean {S.mean(x[0] for x in d):+.3f}   sig<0: {sum(x[2] < 0 for x in d)}/{len(d)}   sig>0: {sum(x[1] > 0 for x in d)}/{len(d)}   worst {min(x[0] for x in d):+.3f}")
for dens in ("s5", "s6"):
    cells = {k: v for k, v in ru.items() if f"ruler2_{dens}_" in k}
    print(f"\nRULER {dens} ({len(cells)} cells), recall difference vs A:")
    for arm in "MSL":
        d = [v["diffs"][f"{arm}-A"] for v in cells.values()]
        print(f"  {arm}-A  mean {S.mean(x[0] for x in d):+.3f}   sig>0: {sum(x[1] > 0 for x in d)}/{len(d)}")
    m = S.mean(v["diffs"]["M-A"][0] for v in cells.values())
    for arm in "SL":
        print(f"  retention {arm} vs M: {S.mean(v['diffs'][f'{arm}-A'][0] for v in cells.values()) / m:.0%}")
    print("  billed tokens (mean over readers with usage): " + "  ".join(
        f"{a}={S.mean(v['arms'][a]['billed'] for v in cells.values() if v['arms'][a]['billed']):.0f}" for a in "AMSL"))
