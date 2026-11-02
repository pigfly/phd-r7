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
}
NEEDLE = "One of the special magic {tv} for {key} is: {value}."
TEMPLATE = ("Some special magic {tv} are hidden within the following text. Make sure to memorize it. I will quiz you about "
            "the {tv} afterwards.\n[The text is rendered in the image above.]\nWhat are all the special magic {tv} for {query} "
            "mentioned in the provided text? Copy each one exactly, character for character. "
            'Return ONLY JSON: {{"ids": [...]}}')
ADJ = "abundant brave calm dusty eager fancy gentle hollow icy jolly keen lively mellow nimble odd plain quiet rapid shiny tidy".split()
NOUN = "apple bridge candle desert engine feather garden harbor island jacket kettle ladder meadow needle orchard pencil quarry river saddle tunnel".split()

def rnd(kind, R):
    if kind == "numbers": return str(R.randint(10 ** 6, 10 ** 7 - 1))
    if kind == "uuids": return str(uuid.UUID(int=R.getrandbits(128), version=4))
    return f"{R.choice(ADJ)}-{R.choice(NOUN)}"

def make(i, cfg, R, sents, chars):
    keys, vals, needles = [], [], []
    while len(keys) < cfg["nk"]:
        k = rnd(cfg["k"], R)
        if k not in keys: keys.append(k)
    for k in keys:
        v = [rnd(cfg["v"], R) for _ in range(cfg["nv"])]; vals.append(v)
        needles += [NEEDLE.format(tv=cfg["v"], key=k, value=x) for x in v]
    R.shuffle(needles)
    if cfg["hay"] == "essay":
        start = R.randrange(len(sents) - 400); body, n = [], 0
        for s in sents[start:]:
            if n + len(s) > chars - sum(len(x) + 1 for x in needles): break
            body.append(s); n += len(s) + 1
        depths = sorted(R.sample(range(len(body) + 1), len(needles)))
        for d, nd in reversed(list(zip(depths, needles))): body.insert(d, nd)
    else:  # haystack made of distractor needles
        body = []
        while sum(len(x) + 1 for x in body) < chars - sum(len(x) + 1 for x in needles):
            body.append(NEEDLE.format(tv=cfg["v"], key=rnd(cfg["k"], R), value=rnd(cfg["v"], R)))
        for nd in needles: body.insert(R.randrange(len(body) + 1), nd)
    q = R.randrange(len(keys))
    return dict(item=i, text=" ".join(body), query=keys[q], answers=vals[q], all_keys=keys,
                prompt=TEMPLATE.format(tv=cfg["v"], query=keys[q]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True); ap.add_argument("--size", type=int, default=6)
    ap.add_argument("--n", type=int, default=25); ap.add_argument("--chars", type=int, default=16000)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--out", required=True)
    a = ap.parse_args(); cfg = TASKS[a.task]; R = random.Random(a.seed); M.REAL = False
    hay = json.loads((HERE / "ruler" / "pg_essays.json").read_text())["text"]
    sents = [s for s in re.split(r"(?<=[.!?])\s+", hay) if 10 < len(s) < 400]
    out = HERE / a.out; (out / "img").mkdir(parents=True, exist_ok=True)
    items = [make(i, cfg, R, sents, a.chars) for i in range(a.n)]; man = []
    for it in items:
        A = M.render(M.units_uniform(it["text"], a.size)); bud = M.vtokens(*A.size)
        C, slo, shi = M.arm_c(it["text"], bud)
        X, xlo, xhi, lead = M.arm_m(it["text"], bud)
        for arm, im, lo, hi, ld in (("A", A, a.size, a.size, 0), ("C", C, slo, shi, 0), ("M", X, xlo, xhi, lead)):
            man.append(dict(item=it["item"], arm=arm, s_lo=lo, s_hi=hi, lead=ld, vtok=M.vtokens(*im.size), wh=im.size, anchor_tok=0, _im=im))
    R.shuffle(man)
    for k, m in enumerate(man):
        m["name"] = f"img{k:03d}"; m.pop("_im").save(out / "img" / f"{m['name']}.png")
        (out / "img" / f"{m['name']}.prompt").write_text(items[m["item"]]["prompt"])
    (out / "gt.json").write_text(json.dumps(dict(task=a.task, size=a.size, items=items), indent=1))
    (out / "manifest.json").write_text(json.dumps(man, indent=1))
    from collections import Counter
    print(a.out, len(man), "images; A vtok", sum(m["vtok"] for m in man if m["arm"] == "A") / a.n,
          *[(x, Counter((m["s_lo"], m["s_hi"]) for m in man if m["arm"] == x).most_common(3)) for x in "CM"],
          "max h", max(m["wh"][1] for m in man))

if __name__ == "__main__":
    main()
