"""Selection-method control (advisor feedback, 2026-11-16).
Same items as niq3_s6 (natural LongBench targets sampled without the detector), same renderer, same vision-token
budget B (typical COC at 6 px) and the same two sizes (prose 5 px, selected strings 12 px). Only the choice of which
strings to enlarge changes. Each selector ranks word types; walking down the ranking, a type is enlarged if the image still fits B, else skipped.
  P  simple rule : tokens that contain a digit or have >= 12 characters, longest first
  Q  surprisal   : tokens of >= 4 characters, highest mean per-character surprisal under Qwen2.5-0.5B first
                   (the residual-entropy estimate of Sec. 3.2, computed on the document text)
The current detector (arm S) and typical COC (arm A) are read from niq3_s6.
usage: python3 sel_control.py --out niq3sel_s6"""
import argparse, json, random, re
from pathlib import Path
import make_items as M
import entropy_map as E

HERE = Path(__file__).parent
ST = ".,;:()[]\"'"
S_LO, S_HI, SIZE = 5, 12, 6

def types(text):
    h = E.surprisal(text); occ = {}; k = 0
    for w in M.words(text):
        if w.strip():
            t = w.strip(ST); a = k + w.find(t)
            if t: occ.setdefault(t, []).append(a)
        k += len(w)
    sur = {t: max(float(h[a:a + len(t)].mean()) for a in v) for t, v in occ.items()}
    return occ, sur

def ranking(arm, occ, sur):
    if arm == "P": return sorted([t for t in occ if re.search(r"\d", t) or len(t) >= 12], key=lambda t: (-len(t), t))
    return sorted([t for t in occ if len(t) >= 4], key=lambda t: (-sur[t], t))

def render_sel(text, sel):
    M.ORACLE = set(sel)
    try: return M.render(M.units_mixed(text, S_LO, S_HI))
    finally: M.ORACLE = None

_CW, _LH = {}, {}
def _metrics(s):
    if s not in _CW: _CW[s] = M.font(s).getlength("M"); _LH[s] = sum(M.font(s).getmetrics()) + 1
    return _CW[s]

def height(units):
    """image height of M.render(units) without drawing (Menlo is monospaced; checked equal to M.render)"""
    total, cur, x = 0, None, M.MARGIN
    for t, s in units:
        w = len(t) * _metrics(s)
        if cur is not None and x + w > M.W - M.MARGIN and t != " ": total += cur; cur, x = None, M.MARGIN
        if cur is None and t == " ": continue
        cur = max(cur or 0, _LH[s]); x += w
    return (total + cur if cur is not None else total) + 2 * M.MARGIN

def fits(text, sel, budget):
    M.ORACLE = set(sel)
    try: return M.vtokens(M.W, height(M.units_mixed(text, S_LO, S_HI))) <= budget
    finally: M.ORACLE = None

def fill(text, rank, budget):
    """walk the ranking and enlarge each string type if the image still fits the budget, otherwise skip it"""
    sel = []
    for t in rank:
        if fits(text, sel + [t], budget): sel.append(t)
    im = render_sel(text, sel); assert M.vtokens(*im.size) <= budget
    return sel, im

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--src", default="niq3_s6"); ap.add_argument("--out", required=True)
    ap.add_argument("--arms", default="PQ"); ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args(); M.REAL = True
    items = json.loads((HERE / a.src / "gt.json").read_text())["items"]
    out = HERE / a.out; (out / "img").mkdir(parents=True, exist_ok=True); man = []
    for it in items:
        text = it["text"]; bud = M.vtokens(*M.render(M.units_uniform(text, SIZE)).size)
        occ, sur = types(text); tgt = it["answers"][0]
        for arm in a.arms:
            rank = ranking(arm, occ, sur); sel, im = fill(text, rank, bud); n = len(sel)
            pages = M.paginate(im)
            man.append(dict(item=it["item"], arm=arm, s_lo=S_LO, s_hi=S_HI, extra=0, vtok=M.vtok_pages(pages), budget=bud,
                            n_pages=len(pages), wh=im.size, anchors=None, n_sel=n, n_cand=len(rank),
                            sel_chars=sum(len(t) * len(occ[t]) for t in sel), target_selected=tgt in set(sel), _im=pages))
        print(it["item"], {m["arm"]: (m["n_sel"], m["sel_chars"], m["target_selected"]) for m in man if m["item"] == it["item"]}, flush=True)
    random.Random(a.seed).shuffle(man)
    for k, m in enumerate(man):
        m["name"] = f"img{k:03d}"
        for j, pg in enumerate(m.pop("_im")): pg.save(out / "img" / (f"{m['name']}.png" if j == 0 else f"{m['name']}.p{j}.png"))
        (out / "img" / f"{m['name']}.prompt").write_text(items[m["item"]]["prompt"])
    (out / "gt.json").write_text(json.dumps(dict(task="niq", size=SIZE, items=items, src=a.src), indent=1))
    (out / "manifest.json").write_text(json.dumps(man, indent=1))
    for arm in a.arms:
        ms = [m for m in man if m["arm"] == arm]
        print(arm, "targets selected", sum(m["target_selected"] for m in ms), "/", len(ms),
              "mean sel chars", round(sum(m["sel_chars"] for m in ms) / len(ms)), "mean vtok", round(sum(m["vtok"] for m in ms) / len(ms)))

if __name__ == "__main__":
    main()
