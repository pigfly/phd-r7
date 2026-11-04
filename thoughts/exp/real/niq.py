"""Natural-identifier verbatim QA (NIQ): long LongBench documents (<= 40K chars) that already contain identifiers
(URLs, ISBNs, report numbers, coordinates, version strings ...). One question per document asks for the exact string
that follows a unique 6-word phrase. Same renderer arms as RULER: A, S, K, X (+ text via run_text.py).
usage: python3 niq.py --n 60 --out niq_s6"""
import argparse, json, random, re
from collections import Counter
from pathlib import Path
import make_items as M

HERE = Path(__file__).parent
TASKS = ["qasper", "multifieldqa_en", "gov_report", "2wikimqa", "hotpotqa", "multi_news"]
PH = "[The text is rendered in the image above.]"
TPL = ("The following text is given.\n{ph}\n\nIn the text, which exact string comes immediately after the words \"{prefix}\"? "
       "Copy it character for character. Return ONLY JSON: {{\"ids\": [\"...\"]}}")
ARTIFACT = re.compile(r"BIBREF|FIGREF|TABREF|SECREF|EQREF|DISPLAYFORM|DISPLAY_FORM|INLINEFORM|[\\{}$^]")
STRIP = ".,;:()[]\"'"
GLUED = re.compile(r",[A-Za-z]|\),|=|[.)\]][A-Z]|\d[a-z]{3,}[A-Z]|[a-z]{2,}\.[a-z]+[0-9]")

def candidates(text, anytarget=False):
    ws = M.words(text); out = []
    toks = [w for w in ws if w.strip()]
    M.STRICT = True; flags = [M.flagged(w) for w in toks]; M.STRICT = False
    for i, (w, f) in enumerate(zip(toks, flags)):
        t = w.strip(STRIP)
        if (not f and not anytarget) or i < 6 or not ((4 if anytarget else 6) <= len(t) <= 64) or not t.isascii() or ARTIFACT.search(t) or not re.search(r"\d", t): continue
        if "?" in t or GLUED.search(t) or not t[0].isalnum(): continue   # dataset artifacts: missing spaces / replaced non-ASCII
        if any(flags[i - 6:i]): continue                      # prefix must be ordinary words
        prefix = " ".join(toks[i - 6:i])
        if text.count(prefix) != 1 or text.count(t) < 1: continue
        out.append((prefix, t, f))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60); ap.add_argument("--size", type=int, default=6)
    ap.add_argument("--seed", type=int, default=21); ap.add_argument("--arms", default="ASKX"); ap.add_argument("--out", required=True)
    ap.add_argument("--items", help="re-render the items of an existing run (gt.json dir) at --size")
    ap.add_argument("--anytarget", action="store_true", help="review RM-5: targets = any digit-bearing token (>=4 chars), "
                    "sampled independently of the detector; whether the detector flags the target is recorded")
    a = ap.parse_args(); R = random.Random(a.seed); M.REAL = True
    per = a.n // len(TASKS); items = []
    if a.items: items = json.loads((HERE / a.items / "gt.json").read_text())["items"]; TASKS_ = []
    else: TASKS_ = TASKS
    for task in TASKS_:
        rows = [json.loads(l) for l in open(HERE / "longbench" / "data" / f"{task}.jsonl")]
        rows = [r for r in rows if len(r["context"]) <= 40000]; R.shuffle(rows); got = 0
        for r in rows:
            if got >= per: break
            text = "".join(c if c.isascii() else "?" for c in re.sub(r"\s+", " ", r["context"]).strip())
            cand = candidates(text, a.anytarget)
            if not cand: continue
            prefix, ans, fl = R.choice(cand)
            items.append(dict(item=len(items), task=task, text=text, answers=[ans], placeholder=PH, flagged=fl,
                              prompt=TPL.format(ph=PH, prefix=prefix), gold=[ans])); got += 1
    out = HERE / a.out; (out / "img").mkdir(parents=True, exist_ok=True); man = []
    for it in items:
        bud = M.vtokens(*M.render(M.units_uniform(it["text"], a.size)).size)
        for arm in a.arms:
            anchors = None
            if arm in "KX":
                im, lo, hi, ex = M.long_arm("A" if arm == "K" else "S", it["text"], bud, a.size); M.STRICT = True
                anchors = [w.strip(STRIP) for w in M.words(it["text"]) if M.flagged(w)]; M.STRICT = False
            else: im, lo, hi, ex = M.long_arm(arm, it["text"], bud, a.size)
            pages = M.paginate(im)
            man.append(dict(item=it["item"], arm=arm, s_lo=lo, s_hi=hi, extra=ex, vtok=M.vtok_pages(pages), n_pages=len(pages),
                            wh=im.size, anchors=anchors, anchor_tok=round(sum(len(t) / 2 + 3 for t in anchors)) if anchors else 0, _im=pages))
    R.shuffle(man)
    for k, m in enumerate(man):
        m["name"] = f"img{k:03d}"
        for j, pg in enumerate(m.pop("_im")): pg.save(out / "img" / (f"{m['name']}.png" if j == 0 else f"{m['name']}.p{j}.png"))
        q = items[m["item"]]["prompt"]
        if m.get("anchors"): q += "\n\nExact strings copied verbatim from the text block in the image:\n" + "\n".join(m["anchors"])
        (out / "img" / f"{m['name']}.prompt").write_text(q)
    (out / "gt.json").write_text(json.dumps(dict(task="niq", size=a.size, items=items), indent=1))
    (out / "manifest.json").write_text(json.dumps(man, indent=1))
    print(a.out, len(items), "items", Counter(i["task"] for i in items), Counter((m["arm"], m["s_lo"], m["s_hi"]) for m in man if m["arm"] == "S").most_common(4),
          "anchors/item", round(sum(len(m["anchors"] or []) for m in man if m["arm"] == "K") / len(items), 1))
    print("targets flagged by the detector:", sum(it.get("flagged", 1) for it in items), "/", len(items))
    for it in items[:6]: print("  ", it["task"], "|", it["prompt"].split("words ")[1][:70], "->", it["answers"][0])

if __name__ == "__main__":
    main()
