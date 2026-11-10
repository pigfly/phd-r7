"""Entropy x glyph-size study (why allocation works): how small can a string be drawn before a black-box VLM can no
longer copy it, as a function of how predictable the string is?  Every item is one RULER-style essay haystack (16K
characters) with one needle "One of the special magic codes for {key} is: {value}." whose value is a 32-character
string of one of three types, from predictable to unpredictable:
  E  a natural English phrase (32 characters cut at word boundaries from LongBench HotpotQA passages)
  W  random common English words joined by spaces (word-level unpredictable, letter-level constrained)
  H  random lowercase hexadecimal (4 bits per character, no constraint)
The haystack, key, and needle position are identical across the three types and across glyph sizes, and the whole
document is rendered uniformly at s px (arm A of the paper). usage: python3 esz.py --out esz --n 20"""
import argparse, json, random, re
from pathlib import Path
import make_items as M
import ruler_niah as RN

HERE = Path(__file__).parent
SIZES = [4, 5, 6, 7, 8, 10]
NEEDLE = "One of the special magic codes for {key} is: {value}."
TPL = ("Some special magic codes are hidden within the following text. Make sure to memorize them. I will quiz you about "
       "the codes afterwards.\n[The text is rendered in the image above.]\nWhat is the special magic code for {key} mentioned "
       "in the provided text? Copy it exactly, character for character, including spaces. "
       'Return ONLY JSON: {{"ids": ["..."]}}')

def english_spans(R, n):
    rows = [json.loads(l) for l in open(HERE / "longbench" / "data" / "hotpotqa.jsonl")]
    out = []
    while len(out) < n:
        ctx = re.sub(r"\s+", " ", R.choice(rows)["context"])
        ws = [w for w in ctx.split(" ") if re.fullmatch(r"[a-z]+", w)]          # lowercase words only
        for _ in range(50):
            i = R.randrange(max(1, len(ws) - 12)); s = ""
            for w in ws[i:i + 12]:
                if len(s) + len(w) + (1 if s else 0) > 32: break
                s = (s + " " + w) if s else w
            if len(s) == 32 and s not in out: out.append(s); break
    return out

def random_words(R, vocab):
    while True:
        s = ""
        while len(s) < 32:
            w = R.choice(vocab); s = (s + " " + w) if s else w
        if len(s) == 32: return s

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="esz"); ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=7); a = ap.parse_args(); R = random.Random(a.seed); M.REAL = False
    hay = json.loads((HERE / "ruler" / "pg_essays.json").read_text())["text"]
    sents = [s for s in re.split(r"(?<=[.!?])\s+", hay) if 10 < len(s) < 400]
    vocab = sorted({w for w in re.findall(r"\b[a-z]{3,8}\b", hay)}, key=lambda w: -hay.count(" " + w + " "))[:2000]
    eng = english_spans(R, a.n)
    items = []
    for i in range(a.n):
        base = RN.make(i, dict(RN.TASKS["niah_single_3"]), R, sents, 16000)   # haystack, key and position from RULER
        uid = next(v for v in base["answers"])
        vals = {"E": eng[i], "W": random_words(R, vocab), "H": "".join(R.choice("0123456789abcdef") for _ in range(32))}
        for t, v in vals.items():
            text = base["text"].replace(f"One of the special magic uuids for {base['query']} is: {uid}.",
                                        NEEDLE.format(key=base["query"], value=v))
            assert v in text
            items.append(dict(item=len(items), base=i, type=t, text=text, query=base["query"], answers=[v],
                              prompt=TPL.format(key=base["query"])))
    out = HERE / a.out; (out / "img").mkdir(parents=True, exist_ok=True); man = []
    for it in items:
        for s in SIZES:
            im = M.render(M.units_uniform(it["text"], s)); pages = M.paginate(im)
            man.append(dict(item=it["item"], base=it["base"], type=it["type"], size=s, arm="A", vtok=M.vtok_pages(pages),
                            n_pages=len(pages), _im=pages))
    R.shuffle(man)
    for k, m in enumerate(man):
        m["name"] = f"img{k:04d}"
        for j, pg in enumerate(m.pop("_im")): pg.save(out / "img" / (f"{m['name']}.png" if j == 0 else f"{m['name']}.p{j}.png"))
        (out / "img" / f"{m['name']}.prompt").write_text(items[m["item"]]["prompt"])
    (out / "gt.json").write_text(json.dumps(dict(task="esz", items=items), indent=1))
    (out / "manifest.json").write_text(json.dumps(man, indent=1))
    from collections import Counter
    print(a.out, len(man), "images", Counter(m["n_pages"] for m in man), {s: round(sum(m["vtok"] for m in man if m["size"] == s) / (3 * a.n)) for s in SIZES})
    for t in "EWH": print(t, [it["answers"][0] for it in items if it["type"] == t][:3])

if __name__ == "__main__":
    main()
