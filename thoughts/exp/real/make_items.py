"""Render synthetic T-A items for the real-VLM pilot (RQ1 + RQ2 in one batch).

Arms (same item text, different rendering):
  A uniform  : one font size, hard character wrap (identifiers may be split across lines)
  B nobreak  : same font size, word wrap (identifiers never split)            -> RQ2
  C hazard   : word wrap; flagged spans at S_HI, prose at the largest size that
               keeps vision tokens <= arm A                                    -> RQ1
Vision-token cost = ceil(w/28) * ceil(h/28) (Claude high-res tier, no resize below 2576 px).

usage: python3 make_items.py --size 8 --n 20 --out run1      (main run)
       python3 make_items.py --calib --out calib              (density calibration)
"""
import argparse, importlib, inspect, json, math, random, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
W = 1008          # 36 patches wide
MARGIN = 4
S_HI = 12         # frozen: flagged-span font size for arm C
CODENAMES = ["marigold", "lantern", "thistle", "juniper", "saffron", "harbor", "quill", "ember",
             "willow", "cobalt", "meadow", "falcon", "pebble", "orchid", "tundra", "velvet",
             "canyon", "sparrow", "glacier", "mosaic", "nectar", "prism", "russet", "zephyr"]

MASCOTS = ["otter", "heron", "badger", "lynx", "walrus", "puffin", "gecko", "bison", "ibis", "marten",
           "koala", "osprey", "tapir", "egret", "ferret", "jackal", "lemur", "magpie", "newt", "quokka"]
SERVERS = ["atlas", "borealis", "cascade", "dynamo", "equinox", "fjord", "granite", "horizon", "indigo", "jasper",
           "kestrel", "lumen", "monsoon", "nimbus", "onyx", "pinnacle", "quasar", "redwood", "summit", "trellis"]
LEAD = 1          # arm L: +1px line spacing on prose-only lines
ANCHOR_BELOW = 10  # CD arm: anchor flagged spans still rendered below this size (frozen from round 2: 8-9px insufficient, 11-12px fine)

_fonts = {}
def font(s):
    k = (FONT_PATH, s)
    if k not in _fonts: _fonts[k] = ImageFont.truetype(FONT_PATH, s)
    return _fonts[k]

def vtokens(w, h): return math.ceil(w / 28) * math.ceil(h / 28)


# ---------------- text ----------------
def prose_pool():
    out = []
    for m in ["decimal", "fractions", "statistics", "calendar", "http.client", "heapq", "difflib", "shutil"]:
        for _, obj in inspect.getmembers(importlib.import_module(m)):
            d = inspect.getdoc(obj)
            if d and len(d) > 60:
                for s in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", d)):
                    if 40 < len(s) < 220 and not re.search(r"[0-9a-f]{6,}|\d{4,}|>>>", s): out.append(s)
    return list(dict.fromkeys(out))

def ident(kind, R):
    hx = lambda n: "".join(R.choice("0123456789abcdef") for _ in range(n))
    return {"hex12": lambda: hx(12),
            "sha16": lambda: hx(16),
            "uuid": lambda: f"{hx(8)}-{hx(4)}-{hx(4)}-{hx(4)}-{hx(12)}",
            "path": lambda: f"/var/log/app_{hx(4)}/run{R.randint(10, 99)}.log",
            "ipport": lambda: f"10.{R.randint(0, 255)}.{R.randint(0, 255)}.{R.randint(1, 254)}:{R.randint(1024, 65535)}",
            "num6": lambda: str(R.randint(100000, 999999))}[kind]()

TEMPL = {"hex12": "Build {} passed.", "sha16": "The commit is {}.", "uuid": "Request id {} was logged.",
         "path": "Output went to {} for review.", "ipport": "The service listens on {} today.",
         "num6": "Ticket {} is still open."}

def make_item(i, pool, R):
    sents = R.sample(pool, 14)
    kinds = list(TEMPL); R.shuffle(kinds)
    ids = [(k, ident(k, R)) for k in kinds]
    code, masc, serv = R.choice(CODENAMES), R.choice(MASCOTS), R.choice(SERVERS)
    probes = [f"The release codename is {code}.", f"The team mascot is a {masc}.", f"The backup server is named {serv}."]
    extra = [TEMPL[k].format(v) for k, v in ids] + probes
    return _assemble(i, sents, extra, [{"kind": k, "value": v} for k, v in ids], code, masc, serv, R)

def _assemble(i, sents, extra, ids, code, masc, serv, R):
    R.shuffle(extra)
    slots = sorted(R.sample(range(1, len(sents)), len(extra)))
    out, j = [], 0
    for n, s in enumerate(sents):
        if j < len(extra) and n == slots[j]: out.append(extra[j]); j += 1
        out.append(s)
    return {"item": i, "text": " ".join(out), "ids": ids, "codename": code, "mascot": masc, "server": serv}

# ---------------- real-distribution items (installed packages: METADATA prose + RECORD lines) ----------------
def real_pools():
    import glob, site, os
    dirs = site.getsitepackages() + [site.getusersitepackages()]
    prose, recs = [], []
    for d in dirs:
        for m in glob.glob(os.path.join(d, "*.dist-info", "METADATA")):
            body = open(m, errors="ignore").read().split("\n\n", 1)[-1]
            body = re.sub(r"```.*?```", " ", body, flags=re.S); body = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", body)
            body = re.sub(r"https?://\S+|[#*`>|=_]{1,}", " ", body); body = re.sub(r"\s+", " ", body)
            for x in re.split(r"(?<=[.!?])\s+", body):
                if 50 < len(x) < 220 and x.isascii() and not HAZ_REAL.search(x): prose.append(x)
        for r in glob.glob(os.path.join(d, "*.dist-info", "RECORD")):
            for ln in open(r, errors="ignore"):
                p = ln.strip().split(",")
                if len(p) == 3 and p[1].startswith("sha256=") and len(p[0]) < 60 and p[0].isascii(): recs.append((p[0], p[1][7:], p[2]))
    return list(dict.fromkeys(prose)), recs

def make_real_item(i, pools, R):
    prose, recs = pools
    sents = R.sample(prose, 13)
    picks = R.sample(recs, 3)
    code, masc, serv = R.choice(CODENAMES), R.choice(MASCOTS), R.choice(SERVERS)
    extra = [f"Manifest entry {p},sha256={h},{n} recorded." for p, h, n in picks] + \
            [f"The release codename is {code}.", f"The team mascot is a {masc}.", f"The backup server is named {serv}."]
    ids = [{"kind": "b64hash", "value": h} for _, h, _ in picks] + [{"kind": "relpath", "value": p} for p, _, _ in picks]
    return _assemble(i, sents, extra, ids, code, masc, serv, R)


# ---------------- hazard detector (paper-style, label-free) ----------------
HAZ = re.compile(r"[0-9a-f]{8,}|\d{4,}|/\S*\d\S*|\d+\.\d+\.\d+\.\d+")
HAZ_REAL = re.compile(r"[0-9a-f]{8,}|\d{4,}|/\S*\d\S*|\d+\.\d+\.\d+\.\d+|\S+/\S+\.\w{1,5}|sha256=|[A-Za-z0-9_\-]{20,}")
def _ent(t):
    from collections import Counter
    c = Counter(t); return -sum(v / len(t) * math.log2(v / len(t)) for v in c.values())
REAL = False
# strict detector (long-text method): no 4-digit numbers (years), long-token rules need letters AND digits
HAZ_STRICT = re.compile(r"[0-9a-f]{8,}|\d{5,}|/\S*\d\S*|\d+\.\d+\.\d+\.\d+|\S+/\S+\.\w{1,5}|sha256=")
STRICT = False
def _idlike(tok): return bool(re.search(r"\d", tok)) and bool(re.search(r"[A-Za-z]", tok))
def flagged(tok):
    if STRICT:
        t = tok.strip(".,;:()[]\"'")
        return bool(HAZ_STRICT.search(t)) or (_idlike(t) and (bool(re.search(r"[A-Za-z0-9_\-]{20,}", t)) or (
            len(t) >= 16 and max(_ent(t[k:k + 16]) for k in range(len(t) - 15)) >= 3.5)))
    if not REAL: return bool(HAZ.search(tok))
    return bool(HAZ_REAL.search(tok)) or (len(tok) >= 16 and max(_ent(tok[k:k + 16]) for k in range(len(tok) - 15)) >= 3.5)


# ---------------- layout + render ----------------
def layout(units, width=W):
    """units: list of (text, size). Greedy flow; returns lines of (x, text, size)."""
    lines, cur, x = [], [], MARGIN
    for t, s in units:
        w = font(s).getlength(t)
        if cur and x + w > width - MARGIN and t != " ":
            lines.append(cur); cur, x = [], MARGIN
        if not cur and t == " ": continue
        cur.append((x, t, s)); x += w
    if cur: lines.append(cur)
    return lines

def render(units, lead=0):
    """lead: extra px of line spacing on prose-only lines (no enlarged unit), arm L."""
    lines = layout(units); lo = min(s for _, s in units)
    heights = [max(sum(font(s).getmetrics()) for _, _, s in ln) + 1 + (lead if all(s == lo for _, _, s in ln) else 0) for ln in lines]
    H = sum(heights) + 2 * MARGIN
    im = Image.new("L", (W, H), 255); d = ImageDraw.Draw(im); y = MARGIN
    for ln, lh in zip(lines, heights):
        asc = max(font(s).getmetrics()[0] for _, _, s in ln)
        for x, t, s in ln: d.text((x, y + asc - font(s).getmetrics()[0]), t, font=font(s), fill=0)
        y += lh
    return im

def units_uniform(text, s): return [(c, s) for c in text]                       # hard char wrap
def words(text): return [t for t in re.split(r"(\s+)", text) if t]
def units_word(text, s, s_hi=None):
    return [(t, s_hi if (s_hi and flagged(t)) else s) for t in words(text)]

SUB = re.compile(r"[\w.\-]*/[\w.\-/]+|[A-Za-z0-9_\-]{16,}|[0-9a-f]{8,}|\d{4,}|\d+\.\d+\.\d+\.\d+(?::\d+)?")
def pieces(tok):
    """C2: split a flagged token into (substring, is_hazard); only regex-hit substrings get enlarged."""
    out, k = [], 0
    for m in SUB.finditer(tok):
        if m.start() > k: out.append((tok[k:m.start()], False))
        out.append((m.group(0), True)); k = m.end()
    if k < len(tok): out.append((tok[k:], False))
    return out if any(h for _, h in out) else [(tok, True)]
def units_mixed(text, s, s_hi):
    """arm M: prose hard char-wrapped like A (no word-wrap slack), flagged tokens kept whole at s_hi."""
    return [u for t in words(text) for u in ([(t, s_hi)] if flagged(t) else [(c, s) for c in t])]
def units_sub(text, s, s_hi):
    return [(p, s_hi if h else s) for t in words(text) for p, h in (pieces(t) if flagged(t) else [(t, False)])]

def arm_c(text, budget, units=units_word, lead=0, lo_max=None):
    for s_hi in range(S_HI, 5, -1):
        for s_lo in range(min(s_hi, lo_max or s_hi), 4, -1):  # prose larger than the uniform size never fits
            im = render(units(text, s_lo, s_hi), lead)
            if vtokens(*im.size) <= budget: return im, s_lo, s_hi
    im = render(units(text, 5, 5), lead); return im, 5, 5


def arm_m(text, budget, lo_max=None):
    """M: prose hard char-wrapped (as A), flagged tokens whole + enlarged; if there is no row slack,
    prose-only lines lose their 1px extra leading. Returns (im, s_lo, s_hi, lead)."""
    im, lo, hi = arm_c(text, budget, units_mixed, lo_max=lo_max)
    if hi > lo: return im, lo, hi, 0
    im, lo, hi = arm_c(text, budget, units_mixed, lead=-1, lo_max=lo_max); return im, lo, hi, -1


UNIFORM_FONTS = ["/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf",
                 "/System/Library/Fonts/Supplemental/Arial Narrow.ttf"]
def arm_u(text, budget):
    """U (best uniform config, Glyph-style config search at matched budget): over fonts, the largest uniform
    char-wrapped size whose image fits the budget. Returns (im, size, font index)."""
    global FONT_PATH
    old, best = FONT_PATH, None
    try:
        for fi, fp in enumerate(UNIFORM_FONTS):
            FONT_PATH = fp
            for sz in range(14, 4, -1):
                im = render(units_uniform(text, sz))
                if vtokens(*im.size) <= budget:
                    if best is None or sz > best[1]: best = (im, sz, fi)
                    break
    finally:
        FONT_PATH = old
    return best

def arm_z(text, budget, s_big=10):
    """Z (render large, then downsample to the budget; DeepSeek-OCR-style resolution compression)."""
    big = render(units_uniform(text, s_big)); f = 1.0
    while True:
        w, h = max(1, round(big.width * f)), max(1, round(big.height * f))
        if vtokens(w, h) <= budget: return big.resize((w, h), Image.LANCZOS), f
        f *= 0.98

def paginate(im, page_h=2016):
    """split a tall image into pages of height <= page_h, cutting only at blank pixel rows"""
    if im.height <= page_h: return [im]
    px = im.load(); blank = [all(px[x, y] == 255 for x in range(0, im.width, 2)) for y in range(im.height)]
    pages, top = [], 0
    while im.height - top > page_h:
        cut = next((y for y in range(top + page_h, top + page_h // 2, -1) if blank[y]), top + page_h)
        pages.append(im.crop((0, top, im.width, cut))); top = cut
    pages.append(im.crop((0, top, im.width, im.height))); return pages
def vtok_pages(pages): return sum(vtokens(*p.size) for p in pages)


KS = [0, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
def arm_mlocal(text, budget, s_a, s_min_hi=10):
    """L (M-local): prose stays at the uniform size s_a; only prose words within K words of a flagged token drop to s_a-1.
    Picks the smallest K (then the largest s_hi >= s_min_hi) that fits the budget; falls back to global M.
    Returns (im, s_lo, s_hi, K) with K=-1 for the fallback."""
    ws = words(text); idx = [i for i, w in enumerate(ws) if flagged(w)]
    if not idx: return render(units_uniform(text, s_a)), s_a, s_a, 0
    dist, j = [], 0
    for i in range(len(ws)):
        while j + 1 < len(idx) and abs(idx[j + 1] - i) <= abs(idx[j] - i): j += 1
        dist.append(abs(idx[j] - i))
    s_lo = max(5, s_a - 1)
    def build(K, hi):
        return render([u for i, w in enumerate(ws) for u in ([(w, hi)] if i in fl else [(c, s_lo if dist[i] <= K else s_a) for c in w])])
    fl = set(idx); best = None
    for hi in range(S_HI, s_min_hi - 1, -1):  # binary search the smallest feasible K for this s_hi
        lo_k, hi_k, found = 0, len(KS) - 1, None
        while lo_k <= hi_k:
            mid = (lo_k + hi_k) // 2; im = build(KS[mid], hi)
            if vtokens(*im.size) <= budget: found = (mid, im); hi_k = mid - 1
            else: lo_k = mid + 1
        if found and (best is None or found[0] < best[0]): best = (found[0], found[1], hi)
    if best: return best[1], s_lo, best[2], KS[best[0]]
    im, lo, hi, _ = arm_m(text, budget); return im, lo, hi, -1


def long_arm(code, text, budget, s_a):
    """Long-text arms -> (im, s_lo, s_hi, extra). A uniform; M global (current detector); S = M with the strict
    detector; L = M-local with the strict detector; U best uniform font/size; Z render-large-then-downsample.
    (K anchors = A image + text sidecar, handled by the generators.) Restores STRICT afterwards."""
    global STRICT
    old = STRICT
    try:
        if code == "A": return render(units_uniform(text, s_a)), s_a, s_a, 0
        if code == "U": im, sz, fi = arm_u(text, budget); return im, sz, sz, fi
        if code == "Z": im, f = arm_z(text, budget); return im, 10, 10, round(f, 3)
        STRICT = code in "SL"
        return arm_mlocal(text, budget, s_a) if code == "L" else arm_m(text, budget, lo_max=s_a)
    finally:
        STRICT = old


def arm_p(text, budget, s_floor):
    """C': prose never below s_floor; enlarge flagged spans as far as the budget allows."""
    for s_hi in range(S_HI, s_floor, -1):
        im = render(units_word(text, s_floor, s_hi))
        if vtokens(*im.size) <= budget: return im, s_floor, s_hi
    return render(units_word(text, s_floor)), s_floor, s_floor


def arm_cd(text, budget):
    """C rendering + text anchors only for flagged tokens still rendered below ANCHOR_BELOW px."""
    im, s_lo, s_hi = arm_c(text, budget)
    anchors = [w.strip(".,;:()") for w in words(text) if flagged(w)] if s_hi < ANCHOR_BELOW else []
    return im, s_lo, s_hi, anchors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=8); ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=7); ap.add_argument("--out", default="run1")
    ap.add_argument("--arms", default="ABC", help="subset of A,B,C,P(C' prose floor),D(A image + text anchors),E(C + residual anchors),F(C2 substring-level enlargement),L(C + prose line spacing),M(prose char-wrap + whole enlarged tokens)")
    ap.add_argument("--real", action="store_true", help="real-distribution items from installed packages")
    ap.add_argument("--calib", action="store_true")
    ap.add_argument("--calib2", action="store_true", help="latin-square extreme densities")
    a = ap.parse_args()
    global REAL
    R = random.Random(a.seed); REAL = a.real
    pool = real_pools() if a.real else prose_pool()
    out = Path(__file__).parent / a.out; (out / "img").mkdir(parents=True, exist_ok=True)
    gt, manifest = [], []
    mk = make_real_item if a.real else make_item
    items = [mk(i, pool, R) for i in range(a.n if not (a.calib or a.calib2) else (2 if a.calib else 4))]
    if a.calib2:  # level = (font size, downscale factor); reader r gets item i at level (i + r) % 4
        LV = [(5, 1.0), (4, 1.0), (8, 0.5), (8, 0.38)]
        for it in items:
            for li, (s, f) in enumerate(LV):
                im = render(units_uniform(it["text"], s))
                if f < 1: im = im.resize((round(im.width * f), round(im.height * f)), Image.LANCZOS)
                r = (li - it["item"]) % 4; name = f"r{r}_i{it['item']}"
                manifest.append(dict(name=name, item=it["item"], arm="A", size=f"{s}x{f}", reader=r, vtok=vtokens(*im.size), wh=im.size))
                im.save(out / "img" / f"{name}.png")
    elif a.calib:  # uniform arm only, several densities
        for it in items:
            for s in [5, 6, 7, 8, 10]:
                im = render(units_uniform(it["text"], s)); name = f"c{it['item']}_s{s}"
                manifest.append(dict(name=name, item=it["item"], arm="A", size=s, vtok=vtokens(*im.size), wh=im.size))
                im.save(out / "img" / f"{name}.png")
    else:
        for it in items:
            tok_flag = [w.strip(".,;:()") for w in words(it["text"]) if flagged(w)]
            A = render(units_uniform(it["text"], a.size)); bud = vtokens(*A.size)
            ims = {"A": (A, a.size, a.size), "D": (A, a.size, a.size)}
            if "B" in a.arms: ims["B"] = (render(units_word(it["text"], a.size)), a.size, a.size)
            if "C" in a.arms: ims["C"] = arm_c(it["text"], bud)
            if "M" in a.arms: ims["M"] = arm_m(it["text"], bud)[:3]
            if "L" in a.arms: ims["L"] = arm_c(it["text"], bud, lead=LEAD)
            if "F" in a.arms: ims["F"] = arm_c(it["text"], bud, units_sub)
            if "P" in a.arms: ims["P"] = arm_p(it["text"], bud, a.size)
            cd_anchors = None
            if "E" in a.arms:  # E = CD (hazard rendering + residual anchors)
                im, slo, shi, cd_anchors = arm_cd(it["text"], bud); ims["E"] = (im, slo, shi)
            for arm in a.arms:
                im, slo, shi = ims[arm]
                anchors = tok_flag if arm == "D" else (cd_anchors or None) if arm == "E" else None
                anc_tok = round(sum(len(t) / 2 + 3 for t in anchors)) if anchors else 0
                manifest.append(dict(item=it["item"], arm=arm, s_lo=slo, s_hi=shi, vtok=vtokens(*im.size), anchor_tok=anc_tok,
                                     wh=im.size, anchors=anchors))
                manifest[-1]["_im"] = im
            it["flagged_tokens"] = tok_flag
        # latin square: reader r sees item i only once, in arm ARMS[(i + r) % 3]
        # blind names: shuffle so the reader cannot infer the arm from the file name
        ARMS = list(a.arms)
        for m in manifest: m["reader"] = (ARMS.index(m["arm"]) - m["item"]) % len(ARMS)
        R.shuffle(manifest)
        for k, m in enumerate(manifest):
            m["name"] = f"r{m['reader']}_img{k:03d}"; m.pop("_im").save(out / "img" / f"{m['name']}.png")
            if m["anchors"]:
                (out / "img" / f"{m['name']}.txt").write_text(
                    "Exact strings copied verbatim from the text block in the image:\n" + "\n".join(m["anchors"]) + "\n")
    for it in items:
        gt.append(it)
    (out / "gt.json").write_text(json.dumps(gt, indent=1))           # never shown to the reader
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"{len(manifest)} images -> {out/'img'}")
    for m in sorted(manifest, key=lambda m: (m["item"], m["arm"]))[:12]: print({k: v for k, v in m.items()})

if __name__ == "__main__":
    main()
