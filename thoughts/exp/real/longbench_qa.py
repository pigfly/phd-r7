"""E3 LongBench QA (Bai et al. 2024) with rendered contexts: does hazard-aware allocation hurt ordinary comprehension?
Official dataset2prompt templates; qa_f1_score; contexts <= --max_chars so one image holds the whole context.
Arms: A uniform, M (default method; general regex+entropy detector). Text-only baseline T via run_text.py (RAW=1).
usage: python3 longbench_qa.py --task multifieldqa_en --n 50 --out lb_s6_mfqa"""
import argparse, json, random, re, string
from collections import Counter
from pathlib import Path
import make_items as M

HERE = Path(__file__).parent
PH = "[The text is rendered in the image above.]"
TPL = {"multifieldqa_en": "Read the following text and answer briefly.\n\n{context}\n\nNow, answer the following question based on the above text, only give me the answer and do not output any other words.\n\nQuestion: {input}\nAnswer:",
       "hotpotqa_e": "Answer the question based on the given passages. Only give me the answer and do not output any other words.\n\nThe following are given passages.\n{context}\n\nAnswer the question based on the given passages. Only give me the answer and do not output any other words.\n\nQuestion: {input}\nAnswer:"}

def normalize(s):  # LongBench metrics.normalize_answer
    s = s.lower(); s = "".join(c for c in s if c not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s); return " ".join(s.split())

def qa_f1(pred, gold):
    p, g = normalize(pred).split(), normalize(gold).split()
    c = sum((Counter(p) & Counter(g)).values())
    if c == 0: return 0.0
    pr, rc = c / len(p), c / len(g); return 2 * pr * rc / (pr + rc)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True); ap.add_argument("--size", type=int, default=6)
    ap.add_argument("--n", type=int, default=50); ap.add_argument("--max_chars", type=int, default=40000)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--out", required=True)
    a = ap.parse_args(); R = random.Random(a.seed); M.REAL = True
    rows = [json.loads(l) for l in open(HERE / "longbench" / "data" / f"{a.task}.jsonl")]
    rows = R.sample([r for r in rows if len(r["context"]) <= a.max_chars], a.n)
    out = HERE / a.out; (out / "img").mkdir(parents=True, exist_ok=True); items, man = [], []
    for i, r in enumerate(rows):
        text = re.sub(r"\s+", " ", r["context"]).strip()
        text = "".join(c if c.isascii() else "?" for c in text)  # Menlo has no CJK etc.; same text for every arm and T
        it = dict(item=i, text=text, answers=r["answers"], input=r["input"], placeholder=PH,
                  prompt=TPL[a.task].format(context=PH, input=r["input"]), n_flagged=sum(M.flagged(w) for w in M.words(text)))
        items.append(it)
        A = M.render(M.units_uniform(text, a.size)); bud = M.vtokens(*A.size)
        X, lo, hi, lead = M.arm_m(text, bud)
        for arm, im, l, h, ld in (("A", A, a.size, a.size, 0), ("M", X, lo, hi, lead)):
            man.append(dict(item=i, arm=arm, s_lo=l, s_hi=h, lead=ld, vtok=M.vtokens(*im.size), wh=im.size, _im=im))
    R.shuffle(man)
    for k, m in enumerate(man):
        m["name"] = f"img{k:03d}"; m.pop("_im").save(out / "img" / f"{m['name']}.png")
        (out / "img" / f"{m['name']}.prompt").write_text(items[m["item"]]["prompt"]); (out / "img" / f"{m['name']}.raw").write_text("")
    (out / "gt.json").write_text(json.dumps(dict(task=a.task, size=a.size, items=items), indent=1))
    (out / "manifest.json").write_text(json.dumps(man, indent=1))
    print(a.out, len(man), "images; A vtok", sum(m["vtok"] for m in man if m["arm"] == "A") / a.n,
          "M sizes", Counter((m["s_lo"], m["s_hi"], m["lead"]) for m in man if m["arm"] == "M").most_common(5),
          "max h", max(m["wh"][1] for m in man), "flagged/item", sum(it["n_flagged"] for it in items) / a.n)

if __name__ == "__main__":
    main()
