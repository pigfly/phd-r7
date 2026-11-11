"""Arm H (Andy feedback, 2026-11-11): partial reallocation. The S allocation, but only a random half of the flagged
strings is enlarged (the other half stays at the prose size). Same items as the Table-1 runs (rbx_*), so A/S/R/U/Z/B
are paired. Gives an intermediate point between uniform rendering and full allocation for the recall-vs-uniformity study.
usage: python3 gen_half.py s6_multivalue s6_multikey_1 ...   -> rhalf_<setting>/"""
import json, random, shutil, sys
from collections import Counter
from pathlib import Path
import make_items as M

HERE = Path(__file__).parent

def main(setting):
    src = HERE / f"rbx_{setting}"; out = HERE / f"rhalf_{setting}"; (out / "img").mkdir(parents=True, exist_ok=True)
    g = json.loads((src / "gt.json").read_text()); size = g["size"]; man = []
    for it in g["items"]:
        bud = M.vtokens(*M.render(M.units_uniform(it["text"], size)).size)
        M.STRICT = True; flag = sorted({w.strip(".,;:()[]\"'") for w in M.words(it["text"]) if M.flagged(w)}); M.STRICT = False
        rr = random.Random(7000 + it["item"]); half = set(rr.sample(flag, len(flag) // 2)) if len(flag) > 1 else set()
        M.ORACLE = half; im, lo, hi, ex = M.long_arm("S", it["text"], bud, size); M.ORACLE = None
        pages = M.paginate(im)
        man.append(dict(item=it["item"], arm="H", s_lo=lo, s_hi=hi, extra=ex, vtok=M.vtok_pages(pages), n_pages=len(pages),
                        wh=im.size, anchor_tok=0, anchors=None, enlarged=sorted(half), n_flagged=len(flag), _im=pages))
    random.Random(1).shuffle(man)
    for k, m in enumerate(man):
        m["name"] = f"img{k:03d}"
        for j, pg in enumerate(m.pop("_im")): pg.save(out / "img" / (f"{m['name']}.png" if j == 0 else f"{m['name']}.p{j}.png"))
        (out / "img" / f"{m['name']}.prompt").write_text(g["items"][[i["item"] for i in g["items"]].index(m["item"])]["prompt"])
    shutil.copy(src / "gt.json", out / "gt.json"); (out / "manifest.json").write_text(json.dumps(man, indent=1))
    print(out.name, len(man), Counter((m["s_lo"], m["s_hi"], m["extra"]) for m in man).most_common(3),
          "flagged", Counter(m["n_flagged"] for m in man), "vtok", sum(m["vtok"] for m in man) / len(man))

if __name__ == "__main__":
    for s in sys.argv[1:]: main(s)
