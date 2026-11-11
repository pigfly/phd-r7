"""Residual-entropy maps and entropy uniformity of rendered documents (Andy feedback, 2026-11-11).

h_i  : per-character residual entropy, estimated text-side as the surprisal -log2 p(c_i | c_<i) under a small causal LM
       (Qwen2.5-0.5B; each token's surprisal is spread evenly over its characters). Cached in entropy_cache/.
rho  : information map of a rendered image = bits per pixel, each character's h_i spread over its glyph cell.
b_j  : bits carried by vision-token cell j (28x28 px, the unit of Eq. 1).
U    : entropy uniformity = mean_j b_j / max_j b_j over cells that hold text; 1 iff every cell carries the same bits.

The glyph cells are recomputed with the exact layout code of make_items.py from manifest.json (arm, sizes, line
leading, font index, downsampling factor), so no image needs to be re-read.
usage: python3 entropy_map.py <run> [...]   -> <run>/entropy.json  {image name: {U, bmax, bmean, ...}}"""
import hashlib, json, math, random, re, sys
from collections import Counter
from pathlib import Path
import numpy as np
import make_items as M

HERE = Path(__file__).parent
CACHE = HERE / "entropy_cache"; CACHE.mkdir(exist_ok=True)
LM = "Qwen/Qwen2.5-0.5B"; CELL = 28
_lm = None

def surprisal(text):
    """per-character surprisal in bits (np.float32 array of len(text))"""
    key = CACHE / (hashlib.sha1(text.encode()).hexdigest()[:20] + ".npy")
    if key.exists(): return np.load(key)
    global _lm
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    if _lm is None:
        dev = "mps" if torch.backends.mps.is_available() else "cpu"
        _lm = (AutoTokenizer.from_pretrained(LM), AutoModelForCausalLM.from_pretrained(LM, dtype=torch.float32).to(dev).eval(), dev)
    tok, lm, dev = _lm
    enc = tok(text, return_offsets_mapping=True, add_special_tokens=False)
    ids, off = enc["input_ids"], enc["offset_mapping"]
    bits = np.zeros(len(ids), np.float32); win, stride = 1024, 512
    bos = tok.bos_token_id if tok.bos_token_id is not None else tok.eos_token_id
    with torch.no_grad():
        for st in range(0, len(ids), stride):  # tokens [st, st+stride) scored with >= win-stride tokens of context
            lo = max(0, st + stride - win); seg = [bos] + ids[lo:st + stride]
            lp = torch.log_softmax(lm(torch.tensor([seg], device=dev)).logits[0, :-1].float(), -1)
            tgt = torch.tensor(seg[1:], device=dev); s = -lp[torch.arange(len(tgt)), tgt] / math.log(2)
            s = s.cpu().numpy(); k0 = st - lo
            bits[st:st + stride] = s[k0:k0 + stride][:len(bits[st:st + stride])]
    h = np.zeros(len(text), np.float32)
    for b, (a, e) in zip(bits, off):
        if e > a: h[a:e] += b / (e - a)
    np.save(key, h); return h

# ---------------- glyph cells ----------------
def _units(text, arm, m, size):
    """-> (list of (unit text, size, char offset), lead, scale, font path) reproducing make_items.long_arm"""
    if arm in ("A", "K") or arm == "U" or arm == "Z":
        s = {"A": size, "K": size, "U": m["s_lo"], "Z": 10}[arm]
        fp = M.UNIFORM_FONTS[m["extra"]] if arm == "U" else M.FONT_PATH
        return [(c, s, i) for i, c in enumerate(text)], 0, (m["extra"] if arm == "Z" else 1.0), fp
    lo, hi = (size, size) if arm == "B" else (m["s_lo"], m["s_hi"])
    lead = m["extra"] if arm in ("S", "X", "R", "O", "Y", "H") else 0
    out, k = [], 0
    for t in M.words(text):
        if M.flagged(t): out.append((t, hi, k))
        else: out += [(c, lo, k + j) for j, c in enumerate(t)]
        k += len(t)
    return out, lead, 1.0, M.FONT_PATH

def cells(text, arm, m, size):
    """-> (boxes float array [n, 4] x0,y0,x1,y1 in final image px, char index array, (W, H))"""
    units, lead, f, fp = _units(text, arm, m, size)
    old = M.FONT_PATH; M.FONT_PATH = fp
    try:
        lines, cur, x = [], [], M.MARGIN
        for t, s, k in units:  # same greedy flow as make_items.layout
            w = M.font(s).getlength(t)
            if cur and x + w > M.W - M.MARGIN and t != " ": lines.append(cur); cur, x = [], M.MARGIN
            if not cur and t == " ": continue
            cur.append((x, t, s, k, w)); x += w
        if cur: lines.append(cur)
        lo = min(s for _, s, _ in units); y = M.MARGIN; bx, ix = [], []
        for ln in lines:
            lh = max(sum(M.font(s).getmetrics()) for _, _, s, _, _ in ln) + 1 + (lead if all(s == lo for _, _, s, _, _ in ln) else 0)
            for x0, t, s, k, w in ln:
                cw = w / len(t)
                for j in range(len(t)): bx.append((x0 + j * cw, y, x0 + (j + 1) * cw, y + lh)); ix.append(k + j)
            y += lh
        H = y + M.MARGIN
    finally:
        M.FONT_PATH = old
    bx = np.array(bx, np.float64) * f
    return bx, np.array(ix), (round(M.W * f), round(H * f))

def info_map(text, arm, m, size, cell=CELL, h=None):
    """-> (b: bits per cell [rows, cols], occupancy: fraction of each cell covered by glyph cells)"""
    h = surprisal(text) if h is None else h
    bx, ix, (Wd, Hd) = cells(text, arm, m, size)
    R, C = math.ceil(Hd / cell), math.ceil(Wd / cell)
    b = np.zeros((R, C)); occ = np.zeros((R, C))
    for (x0, y0, x1, y1), i in zip(bx, ix):  # split each glyph cell's bits over the grid cells it overlaps, by area
        area = max((x1 - x0) * (y1 - y0), 1e-9)
        for r in range(int(y0 // cell), min(R, int(math.ceil(y1 / cell)))):
            oy = min(y1, (r + 1) * cell) - max(y0, r * cell)
            if oy <= 0: continue
            for c in range(int(x0 // cell), min(C, int(math.ceil(x1 / cell)))):
                ox = min(x1, (c + 1) * cell) - max(x0, c * cell)
                if ox > 0: b[r, c] += h[i] * ox * oy / area; occ[r, c] += ox * oy / cell ** 2
    return b, occ

def uniformity(b, occ, min_occ=0.5):
    """U = mean / max of bits per cell over cells at least half covered by text (drops ragged line ends)"""
    v = b[occ >= min_occ]
    if v.size == 0: v = b[b > 0]
    return dict(U=float(v.mean() / v.max()), bmax=float(v.max()), bmean=float(v.mean()), p999=float(np.quantile(v, .999)),
                U999=float(v.mean() / np.quantile(v, .999)), ncell=int(v.size), bits=float(b.sum()))

# ---------------- run-level driver ----------------
def r_pick(it, seed):
    """arm R of ruler_niah.py: random ordinary words matched in total length to the flagged words"""
    M.STRICT = True; ws = M.words(it["text"]); haz = [w for w in ws if M.flagged(w)]; M.STRICT = False
    target = sum(len(w.strip(".,;:()[]\"'")) for w in haz); rr = random.Random(seed * 1000 + it["item"])
    pool = [w.strip(".,;:()[]\"'") for w in ws if w.strip() and w not in haz and len(w.strip(".,;:()[]\"'")) >= 4]
    rr.shuffle(pool); pick, tot = set(), 0
    occ = Counter(w.strip(".,;:()[]\"'") for w in ws if w not in haz)
    for w in pool:
        if tot >= target: break
        if w not in pick and w not in it["gold"] and tot + len(w) * occ[w] <= target * 1.1: pick.add(w); tot += len(w) * occ[w]
    return pick

def find_seed(run, items):
    """recover the generator seed of a RULER run by regenerating its first item"""
    import ruler_niah as RN
    g = json.loads((run / "gt.json").read_text()); cfg = dict(RN.TASKS[g["task"]])
    hay = json.loads((HERE / "ruler" / "pg_essays.json").read_text())["text"]
    sents = [s for s in re.split(r"(?<=[.!?])\s+", hay) if 10 < len(s) < 400]
    for chars in (16000, 32000, 64000, 128000):
        for sd in list(range(100, 130)) + list(range(0, 100)):
            R = random.Random(sd); regen = [RN.make(i, cfg, R, sents, chars) for i in range(len(items))]
            if all(a["text"] == b["text"] for a, b in zip(regen, items)): return sd, {x["item"]: x["gold"] for x in regen}
    return None, None

def run_entropy(run, force=False):
    out = run / "entropy.json"
    if out.exists() and not force: return json.loads(out.read_text())
    g = json.loads((run / "gt.json").read_text()); size = g.get("size", 6)
    items = {it["item"]: it for it in g["items"]}; man = json.loads((run / "manifest.json").read_text())
    seed = None; res = {}
    for m in man:
        it = items[m["item"]]; arm = m["arm"]
        M.STRICT = arm in ("S", "X", "B", "H"); M.ORACLE = None
        if arm == "R":
            if seed is None: seed, golds = find_seed(run, g["items"]); assert seed is not None, run
            gi = dict(it); gi["gold"] = golds[m["item"]]; M.ORACLE = r_pick(gi, seed)
        if arm in ("O", "Y"): M.ORACLE = set(it.get("gold") or it["answers"])
        if arm == "H": M.ORACLE = set(m["enlarged"])
        try:
            b, occ = info_map(it["text"], arm, m, size)
            _, _, (Wd, Hd) = cells(it["text"], arm, m, size)
        finally:
            M.STRICT = False; M.ORACLE = None
        r = uniformity(b, occ); r |= dict(item=m["item"], arm=arm, h_ok=abs(Hd - m["wh"][1]) <= 2)
        res[m["name"]] = r
    out.write_text(json.dumps(res, indent=1)); return res

if __name__ == "__main__":
    for r in sys.argv[1:]:
        res = run_entropy(HERE / r, force=True)
        byarm = {}
        for v in res.values(): byarm.setdefault(v["arm"], []).append(v)
        print(r, {a: (round(np.mean([x["U"] for x in v]), 3), round(np.mean([x["bmax"] for x in v]), 1),
                      f"{sum(x['h_ok'] for x in v)}/{len(v)}") for a, v in sorted(byarm.items())})

# ---------------- reading-order load (v2) ----------------
def char_load(text, arm, m, size, h=None):
    """-> (h, a): per-character bits and glyph area in vision tokens (0 for line-initial spaces that are not drawn)"""
    h = surprisal(text) if h is None else h
    bx, ix, _ = cells(text, arm, m, size)
    a = np.zeros(len(text)); a[ix] = (bx[:, 2] - bx[:, 0]) * (bx[:, 3] - bx[:, 1]) / CELL ** 2
    return h, a

def window_load(h, a, n):
    """load of every n-character reading-order window: bits / vision tokens"""
    ch, ca = np.concatenate([[0], np.cumsum(h)]), np.concatenate([[0], np.cumsum(a)])
    return (ch[n:] - ch[:-n]) / np.maximum(ca[n:] - ca[:-n], 1e-9)
