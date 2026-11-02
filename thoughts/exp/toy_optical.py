"""Toy optical-compression channel (<5 s, CPU, no API, no training of the compressor).

Core hypothesis (RQ1 in ../01_research_questions.md):
  At a FIXED vision budget, spending resolution unevenly -- more pixels on
  text-side-flagged verbatim spans, fewer on prose -- lowers verbatim
  corruption more than (a) uniform rendering and (b) the paper's
  image+anchor sidecar, while prose survives thanks to the language prior.

Model ("reader") = noisy low-res glyph observation + character-bigram prior,
decoded with Viterbi. The bigram is a stand-in for a VLM's language prior;
it is estimated once from stdlib docstrings (no labels, no task data).
This is a mechanism toy, NOT evidence about real VLMs.
"""
import inspect, importlib, json, math, re, sys, time
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

T0 = time.time()
RNG = np.random.default_rng(int(sys.argv[2]) if len(sys.argv) > 2 else 0)
ALPHA = list("abcdefghijklmnopqrstuvwxyz0123456789 .-/_:")
IDX = {c: i for i, c in enumerate(ALPHA)}
K = len(ALPHA)

# ---- exchange rates (assumptions; see 02_micro_experiment.md) ----
PX_PER_VTOKEN = 256           # low-res pixels per vision token
PROSE_CHARS_PER_TTOKEN = 4.0  # BPE on English
VERB_CHARS_PER_TTOKEN = 2.0   # BPE on hex/ids
SIGMA = float(sys.argv[1]) if len(sys.argv) > 1 else 0.10  # encoder noise (frozen after calibration)
LAMBDA = 1.0                  # prior weight
LEVELS = [(4, 2), (5, 3), (6, 3), (7, 4), (8, 4), (10, 5), (12, 6), (14, 7)]  # (h, w) px per char


# ---------------- renderer ----------------
def load_font():
    for p in ["/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Courier.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]:
        if Path(p).exists():
            return ImageFont.truetype(p, 22)
    return ImageFont.load_default(size=22)

FONT = load_font()
HI = []
for c in ALPHA:
    im = Image.new("L", (14, 28), 0)
    ImageDraw.Draw(im).text((0, 0), c, font=FONT, fill=255)
    HI.append(im)

def templates(level):
    h, w = level
    return np.stack([np.asarray(g.resize((w, h), Image.BOX), dtype=np.float32).ravel() / 255 for g in HI])

TPL = {lv: templates(lv) for lv in LEVELS}


# ---------------- language prior (bigram from docstrings) ----------------
def norm(s):
    s = s.lower()
    s = "".join(ch if ch in IDX else " " for ch in s)
    return re.sub(r" +", " ", s)

def docs(mods):
    out = []
    for m in mods:
        mod = importlib.import_module(m)
        for _, obj in inspect.getmembers(mod):
            d = inspect.getdoc(obj)
            if d and len(d) > 40:
                out.append(norm(d))
    return " ".join(dict.fromkeys(out))  # dedupe, keep order

PRIOR_TXT = docs(["collections", "os", "json", "argparse", "logging", "unittest",
                  "subprocess", "threading", "pathlib", "string", "textwrap", "typing"])
TEST_TXT = docs(["decimal", "fractions", "statistics", "calendar", "http.client", "heapq"])
cnt = np.ones((K, K))  # add-one smoothing
for a, b in zip(PRIOR_TXT, PRIOR_TXT[1:]):
    cnt[IDX[a], IDX[b]] += 1
LOGT = np.log(cnt / cnt.sum(1, keepdims=True)).astype(np.float32)
LOG0 = np.log(np.bincount([IDX[c] for c in PRIOR_TXT], minlength=K) + 1.0)
LOG0 = (LOG0 - np.log(np.exp(LOG0).sum())).astype(np.float32)


# ---------------- data: prose with planted verbatim spans ----------------
HEX = "0123456789abcdef"
def rhex(n): return "".join(RNG.choice(list(HEX), n))
GENS = {
    "hex12": lambda: rhex(12),
    "uuid": lambda: f"{rhex(8)}-{rhex(4)}-{rhex(4)}-{rhex(4)}-{rhex(12)}",
    "path": lambda: f"/var/log/app_{rhex(4)}/run{RNG.integers(10, 99)}.log",
    "num6": lambda: str(RNG.integers(100000, 999999)),
}
words = TEST_TXT.split(" ")
stream, spans, pos, w = [], [], 0, 0  # spans: (start, end, kind)
while pos < 24000 and w < len(words) - 30:
    chunk = " ".join(words[w:w + 18]) + " "; w += 18
    kind = list(GENS)[RNG.integers(len(GENS))]
    s = GENS[kind]()
    stream.append(chunk); pos += len(chunk)
    spans.append((pos, pos + len(s), kind)); stream.append(s + " "); pos += len(s) + 1
TEXT = "".join(stream)
Y = np.array([IDX[c] for c in TEXT])
N = len(Y)
is_verb = np.zeros(N, bool)
for a, b, _ in spans: is_verb[a:b] = True


# ---------------- text-side hazard detector (paper-style, label-free) ----------------
def entropy(s):
    c = Counter(s); n = len(s)
    return -sum(v / n * math.log2(v / n) for v in c.values())

HAZ_RE = re.compile(r"[0-9a-f]{8,}|\d{4,}|/\S*\d\S*")
tok_iter = [(m.start(), m.end()) for m in re.finditer(r"\S+", TEXT)]
def tok_score(t):  # continuous score used for AUROC
    digits = sum(ch.isdigit() for ch in t) / len(t)
    return entropy(t) * math.log2(1 + len(t)) * (1 + 2 * digits)
flag = np.zeros(N, bool)
for a, b in tok_iter:
    t = TEXT[a:b]
    if HAZ_RE.search(t) or (len(t) >= 16 and max(entropy(t[i:i + 16]) for i in range(len(t) - 15)) >= 3.5):
        flag[a:b] = True


# ---------------- channel + Viterbi reader ----------------
def observe(level_per_char):
    """Return emission log-lik matrix (N, K)."""
    E = np.empty((N, K), np.float32)
    for lv in set(level_per_char):
        m = np.array([l == lv for l in level_per_char])
        T = TPL[lv]
        obs = T[Y[m]] + RNG.normal(0, SIGMA, (m.sum(), T.shape[1])).astype(np.float32)
        d2 = (obs ** 2).sum(1, keepdims=True) - 2 * obs @ T.T + (T ** 2).sum(1)
        E[m] = -d2 / (2 * SIGMA ** 2)
    return E

def viterbi(E, known=None):
    if known is not None:  # anchors: exact text for these positions
        E = E.copy(); E[known] = -1e9; E[known, Y[known]] = 0
    L = 400; nb = math.ceil(N / L); pad = nb * L - N
    Ep = np.concatenate([E, np.zeros((pad, K), np.float32)]).reshape(nb, L, K)
    dp = Ep[:, 0] + LAMBDA * LOG0; bp = np.empty((nb, L, K), np.int16)
    for t in range(1, L):
        sc = dp[:, :, None] + LAMBDA * LOGT[None]
        bp[:, t] = sc.argmax(1); dp = sc.max(1) + Ep[:, t]
    out = np.empty((nb, L), np.int64); out[:, -1] = dp.argmax(1)
    for t in range(L - 1, 0, -1):
        out[:, t - 1] = bp[np.arange(nb), t, out[:, t]]
    return out.ravel()[:N]


# ---------------- metrics ----------------
FMT = {"hex12": r"[0-9a-f]{12}", "uuid": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
       "path": r"/var/log/app_[0-9a-f]{4}/run\d\d\.log", "num6": r"\d{6}"}
def metrics(pred):
    ok = pred == Y
    exact = [ok[a:b].all() for a, b, _ in spans]
    silent = [(not e) and re.fullmatch(FMT[k], "".join(ALPHA[i] for i in pred[a:b])) is not None
              for (a, b, k), e in zip(spans, exact)]
    return dict(prose_cer=float(1 - ok[~is_verb].mean()), span_exact=float(np.mean(exact)),
                silent_corr=float(np.mean(silent)))

def units_image(levels):
    return sum(h * w for h, w in levels) / PX_PER_VTOKEN

TEXT_UNITS = (~is_verb).sum() / PROSE_CHARS_PER_TTOKEN + is_verb.sum() / VERB_CHARS_PER_TTOKEN
ANCHOR_UNITS = flag.sum() / VERB_CHARS_PER_TTOKEN

def auroc(score, label):
    r = np.argsort(np.argsort(score)) + 1; p = label.sum(); n = len(label) - p
    return float((r[label].sum() - p * (p + 1) / 2) / (p * n)) if p and n else float("nan")

def legible_level(alphabet):  # label-free renderer-side margin: min template distance >= 3 sigma
    ids = [IDX[c] for c in alphabet]
    for lv in LEVELS:
        T = TPL[lv][ids]; d = np.sqrt(((T[:, None] - T[None]) ** 2).sum(-1)); d[np.eye(len(ids), dtype=bool)] = 9e9
        if d.min() >= 3 * SIGMA: return lv
    return LEVELS[-1]

def gated_levels(budget_units, hi):
    """Flagged chars at `hi`, the rest at the largest level fitting the budget."""
    for h in [lv for lv in LEVELS if lv[0] * lv[1] <= hi[0] * hi[1]][::-1]:
        rest = (budget_units * PX_PER_VTOKEN - flag.sum() * h[0] * h[1]) / (~flag).sum()
        fit = [lv for lv in LEVELS if lv[0] * lv[1] <= min(rest, h[0] * h[1])]
        if fit: return [h if f else fit[-1] for f in flag], (fit[-1], h)
    return [LEVELS[0]] * N, (LEVELS[0], LEVELS[0])


# ---- v2: span-length-aware allocation (label-free) ----
EPS = 0.02  # target per-span corruption
def pchar(lv, alphabet=HEX + "-/_."):
    """Union-bound char error from template margins: mean_i sum_j Q(d_ij / 2sigma). Renderer-side, label-free."""
    ids = [IDX[c] for c in alphabet]; T = TPL[lv][ids]
    d = np.sqrt(((T[:, None] - T[None]) ** 2).sum(-1)); np.fill_diagonal(d, np.inf)
    q = 0.5 * np.vectorize(math.erfc)(d / (2 * SIGMA) / math.sqrt(2))
    return float(q.sum(1).mean())
PCHAR = {lv: pchar(lv) for lv in LEVELS}
FLAG_TOK = [(a, b) for a, b in tok_iter if flag[a]]
def need_level(L):
    return next((lv for lv in LEVELS if L * PCHAR[lv] <= EPS), LEVELS[-1])

def gated_v2(budget_units):
    """Each flagged token gets the cheapest level meeting EPS for its length; prose gets the rest.
    If over budget, step every flagged level down one notch until prose fits at >= LEVELS[0]."""
    need = [LEVELS.index(need_level(b - a)) for a, b in FLAG_TOK]
    for shift in range(len(LEVELS)):
        lv_tok = [LEVELS[max(0, i - shift)] for i in need]
        px_flag = sum((b - a) * lv[0] * lv[1] for (a, b), lv in zip(FLAG_TOK, lv_tok))
        rest = (budget_units * PX_PER_VTOKEN - px_flag) / (~flag).sum()
        fit = [lv for lv in LEVELS if lv[0] * lv[1] <= rest]
        if fit:
            levels = [fit[-1]] * N
            for (a, b), lv in zip(FLAG_TOK, lv_tok): levels[a:b] = [lv] * (b - a)
            return levels, (fit[-1], shift)
    return [LEVELS[0]] * N, (LEVELS[0], -1)


# ---------------- run ----------------
res = {"N_chars": int(N), "N_spans": len(spans), "text_units": round(float(TEXT_UNITS), 1)}
gt_tok = np.array([is_verb[a:b].any() for a, b in tok_iter]); fl_tok = np.array([flag[a:b].any() for a, b in tok_iter])
res["detector"] = dict(precision=float((gt_tok & fl_tok).sum() / fl_tok.sum()), recall=float((gt_tok & fl_tok).sum() / gt_tok.sum()))
HI_LV = legible_level(HEX + "-/_.")
res["hi_level_labelfree"] = HI_LV

rows = []
for lv in LEVELS[:6]:
    U = units_image([lv] * N)
    pu = viterbi(observe([lv] * N)); mu = metrics(pu)
    # AUROC: does the text-side token score predict which tokens get corrupted? (C1 analogue)
    err_tok = np.array([(pu[a:b] != Y[a:b]).any() for a, b in tok_iter])
    sc_tok = np.array([tok_score(TEXT[a:b]) for a, b in tok_iter])
    pa = viterbi(observe([lv] * N), known=flag); ma = metrics(pa)                 # paper: image+anchors
    lg, lo = gated_levels(U, HI_LV); mg = metrics(viterbi(observe(lg)))           # ours @ uniform budget
    lg2, lo2 = gated_levels(U + ANCHOR_UNITS, HI_LV); mg2 = metrics(viterbi(observe(lg2)))  # ours @ anchor budget
    lv2, info2 = gated_v2(U); mv2 = metrics(viterbi(observe(lv2)))
    lv3, info3 = gated_v2(U + ANCHOR_UNITS); mv3 = metrics(viterbi(observe(lv3)))
    rows.append(dict(level=lv, chars_per_vtok=round(PX_PER_VTOKEN / (lv[0] * lv[1]), 1),
                     cost_vs_text=dict(uniform=round(U / TEXT_UNITS, 3), anchors=round((U + ANCHOR_UNITS) / TEXT_UNITS, 3),
                                       gated=round(units_image(lg) / TEXT_UNITS, 3), gated_at_anchor_budget=round(units_image(lg2) / TEXT_UNITS, 3),
                                       v2=round(units_image(lv2) / TEXT_UNITS, 3), v2_at_anchor_budget=round(units_image(lv3) / TEXT_UNITS, 3)),
                     auroc_tokscore=round(auroc(sc_tok, err_tok), 3),
                     uniform=mu, anchors=ma, gated=dict(**mg, lo=lo), gated_at_anchor_budget=dict(**mg2, lo=lo2),
                     v2=dict(**mv2, lo_shift=info2), v2_at_anchor_budget=dict(**mv3, lo_shift=info3)))
res["rows"] = rows
res["runtime_s"] = round(time.time() - T0, 2)

def f(m): return f"cer={m['prose_cer']:.3f} exact={m['span_exact']:.3f} silent={m['silent_corr']:.3f}"
print(f"N={N} chars, {len(spans)} spans | detector P={res['detector']['precision']:.3f} R={res['detector']['recall']:.3f} | hi(label-free)={HI_LV}")
for r in rows:
    c = r["cost_vs_text"]
    print(f"\nlevel {r['level']} ({r['chars_per_vtok']} ch/vtok)  AUROC(tok score->err)={r['auroc_tokscore']}")
    print(f"  uniform  cost={c['uniform']:.3f}  {f(r['uniform'])}")
    print(f"  anchors  cost={c['anchors']:.3f}  {f(r['anchors'])}")
    print(f"  gated    cost={c['gated']:.3f}  {f(r['gated'])}  lo={r['gated']['lo']}")
    print(f"  gated@A  cost={c['gated_at_anchor_budget']:.3f}  {f(r['gated_at_anchor_budget'])}  lo={r['gated_at_anchor_budget']['lo']}")
    print(f"  v2       cost={c['v2']:.3f}  {f(r['v2'])}  (lo,shift)={r['v2']['lo_shift']}")
    print(f"  v2@A     cost={c['v2_at_anchor_budget']:.3f}  {f(r['v2_at_anchor_budget'])}  (lo,shift)={r['v2_at_anchor_budget']['lo_shift']}")
print("pchar per level:", {str(k): round(v, 4) for k, v in PCHAR.items()})
print(f"\nruntime {res['runtime_s']} s")
Path(__file__).with_name("results_v1.json").write_text(json.dumps(res, indent=1))
