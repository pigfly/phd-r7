"""Hazard-density sweep (rdens_k*): recall and provider-billed prompt tokens for A / S / K (anchors) / X (S + anchors)
as the number of needles k grows in a 32K-char essay.  usage: python3 analyze_ruler.py; python3 summarize_density.py"""
import json, statistics as S
r = json.load(open("analysis_ruler.json"))
ks = sorted({int(k.split("_k")[1].split("|")[0]) for k in r if k.startswith("rdens_k")})
print(f"{'k':>4s} " + "  ".join(f"{a:>13s}" for a in "ASKX") + "   S-K (S sig worse / better)   X-K   X-A")
for k in ks:
    c = {n: v for n, v in r.items() if n.startswith(f"rdens_k{k}|")}
    def m(a, f): return S.mean(v["arms"][a][f] for v in c.values() if v["arms"][a][f] or f == "recall")
    sk = [v["diffs"]["S-K"] for v in c.values()]
    print(f"{k:4d} " + "  ".join(f"{m(a, 'recall'):.2f} / {m(a, 'billed'):5.0f}" for a in "ASKX")
          + f"   {S.mean(x[0] for x in sk):+.2f} ({sum(x[2] < 0 for x in sk)}/{sum(x[1] > 0 for x in sk)})"
          + f"   {S.mean(v['diffs']['X-K'][0] for v in c.values()):+.2f}   {S.mean(v['diffs']['X-A'][0] for v in c.values()):+.2f}")
print("(cells: mean recall / mean billed prompt tokens over readers that report usage)")
