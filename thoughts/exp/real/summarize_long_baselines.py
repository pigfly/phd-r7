"""Summary of the long-context (rlong_*) and black-box baseline (rbase_*) rounds.
usage: python3 analyze_ruler.py; python3 summarize_long_baselines.py"""
import json, statistics as S
r = json.load(open("analysis_ruler.json"))
print("LONG CONTEXT (6px, arms A/S, text T): mean over 6 readers x 3 tasks")
for L in ("32k", "64k", "128k"):
    c = {k: v for k, v in r.items() if k.startswith(f"rlong_c{L}_")}
    d = [v["diffs"]["S-A"] for v in c.values()]
    tb = [v["arms"]["T"]["billed"] for v in c.values() if v["arms"]["T"]["billed"]]
    print(f"  {L:>4s}: A {S.mean(v['arms']['A']['recall'] for v in c.values()):.2f}  S {S.mean(v['arms']['S']['recall'] for v in c.values()):.2f}  "
          f"S-A {S.mean(x[0] for x in d):+.2f} (sig {sum(x[1] > 0 for x in d)}/{len(d)})  "
          f"billed A {S.mean(v['arms']['A']['billed'] for v in c.values() if v['arms']['A']['billed']):.0f} "
          f"S {S.mean(v['arms']['S']['billed'] for v in c.values() if v['arms']['S']['billed']):.0f} T {S.mean(tb):.0f}")
print("\nBLACK-BOX BASELINES (16K chars): mean over 6 readers x 3 tasks")
for dens in ("s5", "s6"):
    c = {k: v for k, v in r.items() if k.startswith(f"rbase_{dens}_")}
    print(f"  {dens}: " + "  ".join(f"{a} {S.mean(v['arms'][a]['recall'] for v in c.values()):.2f}/"
                                   f"{S.mean(v['arms'][a]['billed'] for v in c.values() if v['arms'][a]['billed']):.0f}" for a in "ASUZK"))
    for k in ("S-U", "S-Z", "S-K"):
        d = [v["diffs"][k] for v in c.values()]
        print(f"    {k}: mean {S.mean(x[0] for x in d):+.3f}  S sig better {sum(x[1] > 0 for x in d)}/{len(d)}  S sig worse {sum(x[2] < 0 for x in d)}/{len(d)}")
