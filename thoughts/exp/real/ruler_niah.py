"""RULER NIAH (Hsieh et al. 2024) re-implemented for rendered contexts; templates / needle format / task configs follow
NVIDIA/RULER scripts/synthetic.yaml + niah.py.  Haystack = Paul Graham essays (RULER URL list, ruler/pg_essays.json).
Arms: A uniform (char wrap), M (prose char-wrap + whole flagged tokens enlarged), C hazard (same label-free detector + allocation as make_items.py, vision tokens <= A).
usage: python3 ruler_niah.py --task niah_single_3 --size 6 --n 25 --out ruler_s6_single3"""
import argparse, json, random, re, uuid
from pathlib import Path
import make_items as M

HERE = Path(__file__).parent
TASKS = {  # RULER synthetic.yaml
    "niah_single_3":   dict(hay="essay", k="words", v="uuids", nk=1, nv=1, nq=1),
    "niah_multikey_1": dict(hay="essay", k="words", v="numbers", nk=4, nv=1, nq=1),
    "niah_multivalue": dict(hay="essay", k="words", v="numbers", nk=1, nv=4, nq=1),
    "niah_multikey_3": dict(hay="needle", k="uuids", v="uuids", nk=1, nv=1, nq=1),
    # hazard-density sweep (ours): essay haystack with --nk word->uuid needles, one queried key
    "niah_density":    dict(hay="essay", k="words", v="uuids", nk=1, nv=1, nq=1),
    # detector ablation (ours): multivalue with 4-digit values, which the strict detector deliberately does not flag
    "niah_multivalue4": dict(hay="essay", k="words", v="numbers4", nk=1, nv=4, nq=1),
}
NEEDLE = "One of the special magic {tv} for {key} is: {value}."
TV = {"numbers4": "numbers"}  # surface name used in the needle / question
TEMPLATE = ("Some special magic {tv} are hidden within the following text. Make sure to memorize it. I will quiz you about "
            "the {tv} afterwards.\n[The text is rendered in the image above.]\nWhat are all the special magic {tv} for {query} "
            "mentioned in the provided text? Copy each one exactly, character for character. "
            'Return ONLY JSON: {{"ids": [...]}}')
ADJ = "abundant brave calm dusty eager fancy gentle hollow icy jolly keen lively mellow nimble odd plain quiet rapid shiny tidy".split()
NOUN = "apple bridge candle desert engine feather garden harbor island jacket kettle ladder meadow needle orchard pencil quarry river saddle tunnel".split()

def rnd(kind, R):
    if kind == "numbers": return str(R.randint(10 ** 6, 10 ** 7 - 1))
    if kind == "numbers4": return str(R.randint(1000, 9999))
    if kind == "uuids": return str(uuid.UUID(int=R.getrandbits(128), version=4))
    return f"{R.choice(ADJ)}-{R.choice(NOUN)}"

def make(i, cfg, R, sents, chars):
    keys, vals, needles = [], [], []
    while len(keys) < cfg["nk"]:
        k = rnd(cfg["k"], R)
        if k not in keys: keys.append(k)
    for k in keys:
        v = [rnd(cfg["v"], R) for _ in range(cfg["nv"])]; vals.append(v)
        needles += [NEEDLE.format(tv=TV.get(cfg["v"], cfg["v"]), key=k, value=x) for x in v]
    R.shuffle(needles)
    if cfg["hay"] == "essay":
        start = R.randrange(max(1, len(sents) - chars // 40)); body, n = [], 0
        for s in sents[start:]:
            if n + len(s) > chars - sum(len(x) + 1 for x in needles): break
            body.append(s); n += len(s) + 1
        depths = (sorted(R.sample(range(len(body) + 1), len(needles))) if len(needles) <= len(body) + 1
                  else sorted(R.choice(range(len(body) + 1)) for _ in needles))  # dense sweep: several needles per gap
        for d, nd in reversed(list(zip(depths, needles))): body.insert(d, nd)
    else:  # haystack made of distractor needles
        body = []
        while sum(len(x) + 1 for x in body) < chars - sum(len(x) + 1 for x in needles):
            body.append(NEEDLE.format(tv=cfg["v"], key=rnd(cfg["k"], R), value=rnd(cfg["v"], R)))
        for nd in needles: body.insert(R.randrange(len(body) + 1), nd)
    q = R.randrange(len(keys))
    return dict(item=i, text=" ".join(body), query=keys[q], answers=vals[q], all_keys=keys,
                prompt=TEMPLATE.format(tv=TV.get(cfg["v"], cfg["v"]), query=keys[q]), gold=[x for v in vals for x in v])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True); ap.add_argument("--size", type=int, default=6)
    ap.add_argument("--n", type=int, default=25); ap.add_argument("--chars", type=int, default=16000)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--out", required=True)
    ap.add_argument("--nk", type=int, default=0, help="override the number of needle keys (density sweep)")
    ap.add_argument("--arms", default="ACM", help="A uniform, C hazard (word wrap), M global, S strict-detector M (default method), "
                    "L M-local, U best uniform font/size, Z render-large-then-downsample, K anchors (A image + verbatim sidecar), "
                    "X = S image + anchors, R = ablation enlarging random ordinary words, O = S with an oracle detector (gold needle values), Y = O image + oracle anchors")
    a = ap.parse_args(); cfg = dict(TASKS[a.task]); R = random.Random(a.seed); M.REAL = False
    if a.nk: cfg["nk"] = a.nk
    hay = json.loads((HERE / "ruler" / "pg_essays.json").read_text())["text"]
    sents = [s for s in re.split(r"(?<=[.!?])\s+", hay) if 10 < len(s) < 400]
    out = HERE / a.out; (out / "img").mkdir(parents=True, exist_ok=True)
    items = [make(i, cfg, R, sents, a.chars) for i in range(a.n)]; man = []
    for it in items:
        bud = M.vtokens(*M.render(M.units_uniform(it["text"], a.size)).size)
        for arm in a.arms:
            anchors = None
            if arm == "C": im, lo, hi = M.arm_c(it["text"], bud); ex = 0
            elif arm in "KXY":  # anchors on the A image (K), the S image (X), or the oracle-S image with oracle anchors (Y)
                if arm == "Y": M.ORACLE = set(it["gold"])
                im, lo, hi, ex = M.long_arm("A" if arm == "K" else "S", it["text"], bud, a.size); M.STRICT = True
                anchors = [w.strip(".,;:()[]\"'") for w in M.words(it["text"]) if M.flagged(w)]; M.STRICT = False; M.ORACLE = None
            elif arm == "R":  # ablation: enlarge random ordinary words with the same total length as the flagged words
                M.STRICT = True; ws = M.words(it["text"]); haz = [w for w in ws if M.flagged(w)]; M.STRICT = False
                target = sum(len(w.strip(".,;:()[]\"'")) for w in haz); rr = random.Random(a.seed * 1000 + it["item"])
                pool = [w.strip(".,;:()[]\"'") for w in ws if w.strip() and w not in haz and len(w.strip(".,;:()[]\"'")) >= 4]
                rr.shuffle(pool); pick, tot = set(), 0
                occ = __import__("collections").Counter(w.strip(".,;:()[]\"'") for w in ws if w not in haz)
                for w in pool:  # match the total length of ALL enlarged occurrences, not of distinct word types
                    if tot >= target: break
                    if w not in pick and w not in it["gold"] and tot + len(w) * occ[w] <= target * 1.1:
                        pick.add(w); tot += len(w) * occ[w]
                M.ORACLE = pick; im, lo, hi, ex = M.long_arm("S", it["text"], bud, a.size); M.ORACLE = None
            elif arm == "O":  # oracle detector: S allocation with exactly the gold needle values flagged
                M.ORACLE = set(it["gold"]); im, lo, hi, ex = M.long_arm("S", it["text"], bud, a.size); M.ORACLE = None
            else: im, lo, hi, ex = M.long_arm(arm, it["text"], bud, a.size)
            pages = M.paginate(im)
            man.append(dict(item=it["item"], arm=arm, s_lo=lo, s_hi=hi, extra=ex, vtok=M.vtok_pages(pages), n_pages=len(pages),
                            wh=im.size, anchor_tok=round(sum(len(t) / 2 + 3 for t in anchors)) if anchors else 0,
                            anchors=anchors, _im=pages))
    R.shuffle(man)
    for k, m in enumerate(man):
        m["name"] = f"img{k:03d}"
        for j, pg in enumerate(m.pop("_im")): pg.save(out / "img" / (f"{m['name']}.png" if j == 0 else f"{m['name']}.p{j}.png"))
        q = items[m["item"]]["prompt"]
        if m.get("anchors"): q += "\n\nExact strings copied verbatim from the text block in the image:\n" + "\n".join(m["anchors"])
        (out / "img" / f"{m['name']}.prompt").write_text(q)
    (out / "gt.json").write_text(json.dumps(dict(task=a.task, size=a.size, items=items), indent=1))
    (out / "manifest.json").write_text(json.dumps(man, indent=1))
    from collections import Counter
    print(a.out, len(man), "images; A vtok", sum(m["vtok"] for m in man if m["arm"] == "A") / a.n,
          *[(x, Counter((m["s_lo"], m["s_hi"], m["extra"]) for m in man if m["arm"] == x).most_common(4)) for x in a.arms if x != "A"],
          "max h", max(m["wh"][1] for m in man), "pages", Counter(m["n_pages"] for m in man),
          "vtok", {x: round(sum(m["vtok"] for m in man if m["arm"] == x) / a.n) for x in a.arms})

if __name__ == "__main__":
    main()
