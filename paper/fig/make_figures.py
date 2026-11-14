"""Figures for the paper. All numbers come from paper/data/numbers.json (built by extract_numbers.py);
teaser crops come from the rendered images of thoughts/exp/real/rlong_c32k_single_3 (item 1).
usage: python3 paper/fig/make_figures.py   -> paper/fig/*.pdf"""

import json, re, sys
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FIG = Path(__file__).resolve().parent
EXP = ROOT / "thoughts" / "exp" / "real"
sys.path.insert(0, str(EXP))
N = json.loads((ROOT / "paper" / "data" / "numbers.json").read_text())

# Academic Figure Skill Typography Baseline — COPY VERBATIM, place at TOP of script
import matplotlib as mpl

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans"],
        "font.size": 8,
        "axes.titlesize": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 8,
        "figure.titlesize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "legend.frameon": False,
    }
)
# Academic Figure Skill Nature/Cell/Science Color Palette -- COPY VERBATIM
CATEGORICAL = ["#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666"]
CATEGORICAL_EXTENDED = [
    "#2166AC",
    "#B2182B",
    "#1B7837",
    "#F1A340",
    "#762A83",
    "#666666",
    "#4393C3",
    "#D6604D",
    "#5AAE61",
    "#B35806",
    "#9970AB",
    "#999999",
]
DIVERGING = ["#2166AC", "#F7F7F7", "#B2182B"]
SEQUENTIAL = ["#F7FBFF", "#6BAED6", "#08306B"]
ACCENT_RED = "#B2182B"
GREY = "#999999"
BLACK = "#222222"
# Academic Figure Skill Export Baseline — COPY VERBATIM
mpl.rcParams.update(
    {
        "pdf.fonttype": 42,  # TrueType font embedding
        "svg.fonttype": "none",  # editable text in SVG
        "savefig.bbox": "tight",  # trim whitespace
        "savefig.dpi": 300,
    }
)


def save_cns_figure(fig, filename):
    """Standard Academic Figure Skill export: vector PDF + 300dpi PNG preview."""
    fig.savefig(f"{filename}.pdf", bbox_inches="tight", dpi=300)
    fig.savefig(f"{filename}.png", bbox_inches="tight", dpi=300)


# semantic roles (one meaning per colour across all figures): COC = grey reference, EquiPix = red accent,
# anchors on COC = blue, EquiPix + anchors = purple, plain text = black
C = dict(A="#666666", K=CATEGORICAL[0], S=ACCENT_RED, X=CATEGORICAL[4], T=BLACK)
MK = dict(A="o", K="s", S="D", X="^", T="*")
LS = dict(A="--", K="-", S="-", X="-", T=":")
NAME = "EquiPix"
LAB = dict(
    A="COC", K="COC+anchor", S="EquiPix (ours)", X="EquiPix+anchor", T="Plain text"
)
INK, MUTED, GRID = BLACK, "#555555", "#E0E0E0"
LIGHT = dict(
    aqua="#BFE6EA", peach="#F7D8B8", mist="#D9E2EB", warm="#F2F2F2", salmon="#F6A69A"
)
MM = 1 / 25.4
TEXTW = 174 * MM
COLW = 84 * MM  # CVPR text width 6.875 in, column width 3.31 in
plt.rcParams.update({"lines.linewidth": 1.2, "lines.markersize": 4})


def style(ax):
    """skill default: no gridlines; if needed, very light grey (#E0E0E0, lw 0.3, alpha 0.5)"""
    ax.grid(True, color=GRID, lw=0.3, alpha=0.5)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------- teaser
def needle_crop(img_path, text, units, lead, answer, width=330, lines_ctx=5):
    import make_items as M

    lines = M.layout(units)
    heights = [
        max(sum(M.font(s).getmetrics()) for _, _, s in ln)
        + 1
        + (lead if all(s == min(x for _, x in units) for _, _, s in ln) else 0)
        for ln in lines
    ]
    flat, y = "", M.MARGIN
    pos = []
    for ln, h in zip(lines, heights):
        pos.append((len(flat), y, h))
        flat += "".join(t for _, t, _ in ln)
        y += h
    i = flat.find(answer)
    li = max(n for n, (o, _, _) in enumerate(pos) if o <= i)
    # x of the answer inside its line
    ln = lines[li]
    acc = pos[li][0]
    x0 = None
    for x, t, s in ln:
        if acc <= i < acc + len(t):
            x0 = x
            break
        acc += len(t)
    im = Image.open(img_path).convert("L")
    top = pos[max(0, li - lines_ctx)][1]
    bot = (
        pos[min(len(pos) - 1, li + lines_ctx)][1]
        + pos[min(len(pos) - 1, li + lines_ctx)][2]
    )
    left = max(0, min(im.width - width, x0 - 40))
    return im.crop((left, top, left + width, bot))


def teaser_old():
    import make_items as M

    run = EXP / "rlong_c32k_single_3"
    gt = {it["item"]: it for it in json.loads((run / "gt.json").read_text())["items"]}
    man = {
        (m["item"], m["arm"]): m
        for m in json.loads((run / "manifest.json").read_text())
    }
    it = gt[1]
    gold = it["answers"][0]
    pa = json.loads((run / "pred_or_claude-sonnet-5.5.json").read_text())
    ma, ms = man[(1, "A")], man[(1, "S")]
    ans_a, ans_s = pa[ma["name"] + ".png"]["ids"][0], pa[ms["name"] + ".png"]["ids"][0]
    M.REAL = False
    crop_a = needle_crop(
        run / "img" / f"{ma['name']}.png",
        it["text"],
        M.units_uniform(it["text"], 6),
        0,
        gold,
    )
    zoom_a = needle_crop(
        run / "img" / f"{ma['name']}.png",
        it["text"],
        M.units_uniform(it["text"], 6),
        0,
        gold,
        width=300,
        lines_ctx=0,
    )
    M.STRICT = True
    crop_s = needle_crop(
        run / "img" / f"{ms['name']}.png",
        it["text"],
        M.units_mixed(it["text"], ms["s_lo"], ms["s_hi"]),
        ms["extra"],
        gold,
    )
    zoom_s = needle_crop(
        run / "img" / f"{ms['name']}.png",
        it["text"],
        M.units_mixed(it["text"], ms["s_lo"], ms["s_hi"]),
        ms["extra"],
        gold,
        width=300,
        lines_ctx=0,
    )
    M.STRICT = False
    fig = plt.figure(figsize=(6.9, 2.45))
    gs = fig.add_gridspec(
        3,
        3,
        width_ratios=[1.0, 1.0, 0.8],
        height_ratios=[1, 0.3, 0.42],
        wspace=0.2,
        hspace=0.12,
        left=0.01,
        right=0.99,
        top=0.91,
        bottom=0.15,
    )
    for col, (crop, zoom, title, ans, ok, arm) in enumerate(
        [
            (crop_a, zoom_a, "Uniform rendering (6 px everywhere)", ans_a, False, "A"),
            (
                crop_s,
                zoom_s,
                "Hazard-aware rendering (ours, same budget)",
                ans_s,
                True,
                "S",
            ),
        ]
    ):
        ax = fig.add_subplot(gs[0, col])
        ax.imshow(crop, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(True)
            sp.set_color(C[arm])
            sp.set_linewidth(1.2)
        ax.set_title(title, fontsize=8, color=INK, pad=3)
        zx = fig.add_subplot(gs[1, col])
        zx.imshow(
            zoom, cmap="gray", vmin=0, vmax=255, interpolation="nearest", aspect="equal"
        )
        zx.set_xticks([])
        zx.set_yticks([])
        for sp in zx.spines.values():
            sp.set_visible(True)
            sp.set_color(C[arm])
            sp.set_linewidth(0.8)
            sp.set_linestyle(":")
        tx = fig.add_subplot(gs[2, col])
        tx.axis("off")
        tx.text(
            0.0,
            0.78,
            f"Q: the special magic uuid for '{it['query']}'?",
            fontsize=6.3,
            color=MUTED,
            transform=tx.transAxes,
        )
        # answer with wrong characters marked
        x = 0.0
        tx.text(x, 0.42, "A:", fontsize=6.6, family="monospace", transform=tx.transAxes)
        x += 0.05
        for a, g in zip(ans, gold):
            tx.text(
                x,
                0.42,
                a,
                fontsize=6.6,
                family="monospace",
                transform=tx.transAxes,
                color=(C["X"] if a != g else INK),
                fontweight=("bold" if a != g else "normal"),
            )
            x += 0.0255
        nwrong = sum(a != g for a, g in zip(ans, gold))
        tx.text(
            0.0,
            0.02,
            (
                "correct"
                if ok
                else f"{nwrong} characters wrong, well-formed, no abstention (silent error)"
            ),
            fontsize=6.3,
            transform=tx.transAxes,
            color=(C["K"] if ok else C["X"]),
        )
    ax = fig.add_subplot(gs[:, 2])
    style(ax)
    Ls = ["32k", "64k", "128k"]
    xs = [32, 64, 128]
    for arm in "AS":
        ys = [m5(L, arm) for L in Ls]
        ax.plot(
            xs,
            ys,
            color=C[arm],
            ls=LS[arm],
            marker=MK[arm],
            label=LAB[arm],
            mfc=("white" if arm == "A" else C[arm]),
        )
    ax.set_xscale("log", base=2)
    ax.set_xticks(xs)
    ax.set_xticklabels(["32K", "64K", "128K"])
    ax.set_ylim(0, 0.8)
    ax.set_xlabel("context length (characters)")
    ax.set_ylabel("needle recall (5 VLMs)")
    ax.legend(
        loc="center left", frameon=False, bbox_to_anchor=(0.02, 0.42), handlelength=1.8
    )
    ax.set_title("Equal vision-token budget", fontsize=7.5, pad=3)
    fig.savefig(FIG / "teaser.pdf")
    plt.close(fig)
    return ans_a, ans_s, gold


# ---------------------------------------------------------------- teaser (v2): information maps + recall vs uniformity
CH = dict(coc="#666666", R=CATEGORICAL[0], H=CATEGORICAL[3], S=ACCENT_RED)


def load_raster(text, arm, m, size, n=48):
    """per-pixel information load: every glyph cell painted with the load (bits / vision token) of the n-character
    reading-order window centred on it; NaN where nothing is drawn"""
    import numpy as np, entropy_map as E

    h, a = E.char_load(text, arm, m, size)
    w = E.window_load(h, a, n)
    lc = np.concatenate(
        [np.full(n // 2, w[0]), w, np.full(len(text) - len(w) - n // 2, w[-1])]
    )
    bx, ix, (Wd, Hd) = E.cells(text, arm, m, size)
    R = np.full((Hd, Wd), np.nan)
    for (x0, y0, x1, y1), i in zip(bx, ix):
        R[int(y0) : int(np.ceil(y1)), int(x0) : int(np.ceil(x1))] = lc[i]
    return R


def token_cells(R, cell=28):
    """vision-token grid of a load raster: each 28x28 cell gets the highest load of the text it contains (NaN if empty)"""
    import numpy as np

    H, W = R.shape
    rows, cols = -(-H // cell), -(-W // cell)
    P = np.full((rows * cell, cols * cell), np.nan)
    P[:H, :W] = R
    B = P.reshape(rows, cell, cols, cell).transpose(0, 2, 1, 3).reshape(rows, cols, -1)
    with np.errstate(all="ignore"):
        out = np.nanmax(B, axis=2)
    return out


# one information-map style for every figure (teaser, pipeline thumbnails, natural document)
MAP_VMIN, MAP_VMAX, MAP_EDGE = 0.0, 1.0, 0.15
MAP_REF = 3.0  # normalized load = (load / page mean) / MAP_REF, clipped to [0, 1]: one fixed scale for every map, no per-map min-max
MAP_LABEL = "normalized information load (0\u20131)"


def map_cmap():
    c = plt.get_cmap("Reds").copy()
    c.set_bad("white")
    return c  # heatmap asset: cmap="Reds"


def page_map(text, arm, m, size=6):
    """vision-token grid of the normalized load (load / page mean / MAP_REF, clipped to 1); M.STRICT / M.ORACLE set by the caller"""
    import numpy as np

    R = load_raster(text, arm, m, size)
    return np.clip(token_cells(R / np.nanmean(R)) / MAP_REF, 0, 1)


def draw_map(ax, G, alpha=1.0, zorder=1):
    import numpy as np

    return ax.pcolormesh(
        np.ma.masked_invalid(G),
        cmap=map_cmap(),
        vmin=MAP_VMIN,
        vmax=MAP_VMAX,
        edgecolors="white",
        linewidth=MAP_EDGE,
        alpha=alpha,
        zorder=zorder,
    )


def map_colorbar(fig, rect, label=MAP_LABEL, fontsize=6.5):
    cax = fig.add_axes(rect)
    sm = plt.cm.ScalarMappable(cmap=map_cmap(), norm=plt.Normalize(MAP_VMIN, MAP_VMAX))
    cb = fig.colorbar(
        sm, cax=cax, orientation="horizontal", ticks=[0, 0.25, 0.5, 0.75, 1]
    )
    cb.ax.set_xticklabels(["0", "0.25", "0.5", "0.75", "1"])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=6, length=2, pad=1)
    cax.text(
        1.04,
        0.5,
        label,
        transform=cax.transAxes,
        fontsize=fontsize,
        va="center",
        color=MUTED,
    )
    return cb


# Academic Figure Skill Asset Confirmation (verified against assets/figures/)
# (teaser, maps) heatmap -> assets/figures/heatmap/plot_composition.py -> param inherit (cmap "Reds", white cell
#                 borders, colorbar with explicit ticks); data are per-page load grids, not a category matrix
# (teaser, scatter) scatter -> cross-type inherit (basic scatter: marker s=10-20, direct labels, no legend box)
def teaser(item=14, out="teaser", task="multivalue"):
    """Card layout (one card per rendering + recall vs U): title, rendered crop, arrow, information map drawn to scale
    (same cell = one vision token), token count. Needles are outlined: red if enlarged, black if not.
    """
    import numpy as np, make_items as M, entropy_map as E
    from stats_pooled import merged
    import statistics as St
    from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch

    U = json.loads((EXP / "analysis_uniformity.json").read_text())
    run_b, run_h = EXP / f"rbx_s6_{task}", EXP / f"rhalf_s6_{task}"
    it = next(
        i
        for i in json.loads((run_b / "gt.json").read_text())["items"]
        if i["item"] == item
    )
    mb = {
        m["arm"]: m
        for m in json.loads((run_b / "manifest.json").read_text())
        if m["item"] == item
    }
    mh = next(
        m
        for m in json.loads((run_h / "manifest.json").read_text())
        if m["item"] == item
    )
    vals = re.findall(r"is: (\d{7})\.", it["text"])
    # middle panel: an illustrative partial reallocation (rendered here, not evaluated): all needles at 12 px, the first
    # fifth of the prose kept at 6 px and the rest at 5 px
    text = it["text"]
    cut = len(text) // 5
    old_units = E._units

    def units_i(tx, arm, m, size):
        if arm != "I":
            return old_units(tx, arm, m, size)
        out, k = [], 0
        for w in M.words(tx):
            if w.strip(".,;:()[]\"'") in vals:
                out.append((w, 12, k))
            else:
                out += [(ch, 6 if k + j < cut else 5, k + j) for j, ch in enumerate(w)]
            k += len(w)
        return out, 0, 1.0, M.FONT_PATH

    E._units = units_i
    mi = {"name": None}
    low = set(vals)
    cols = [
        ("A", mb["A"], run_b, "COC (typical)", "all text at 6 px"),
        ("I", mi, None, "Partial (illustrative)", "needles 12 px, most prose 5 px"),
        ("S", mb["S"], run_b, f"{NAME} (ours)", "prose 5 px, 4 of 4 needles at 12 px"),
    ]
    dd = merged(
        [f"rbx_s6_{t}+rhalf_s6_{t}" for t in ("multikey_1", "multivalue")]
    )  # same 50 documents for all columns
    rec = {
        a: St.mean(
            v[a]["recall"]
            for run in dd.values()
            for rows in run.values()
            for v in rows.values()
            if a in v
        )
        for a in "AHS"
    }
    CROP = {}
    panels = []
    for arm, m, run, *_ in cols:
        M.STRICT = arm in "SH"
        M.ORACLE = (low if arm == "I" else set(mh["enlarged"])) if arm in "HI" else None
        G = page_map(it["text"], arm, m)
        bxs, ixs, _ = E.cells(it["text"], arm, m, 6)
        M.STRICT = False
        M.ORACLE = None
        ixs = list(ixs)
        if arm == "I":
            M.ORACLE = low
            hh, aa = E.char_load(text, "I", m, 6)
            ww = E.window_load(hh, aa, 48)
            UI = (hh.sum() / aa.sum()) / np.sort(ww)[-160:].mean()
            im = np.array(
                M.render([(t, z) for t, z, _ in units_i(text, "I", m, 6)[0]]).convert(
                    "L"
                )
            )
            M.ORACLE = None
        else:
            im = np.array(
                Image.open(
                    Path(str(run).replace("rbx_", "rbase_"))
                    / "img"
                    / f"{m['name']}.png"
                ).convert("L")
            )
        nd = []
        for (
            v
        ) in (
            vals
        ):  # one box per text line, so a needle wrapped across two lines gets two boxes
            j = ixs.index(it["text"].find(v))
            enl = (
                arm == "S"
                or (arm == "H" and v in mh["enlarged"])
                or (arm == "I" and v in low)
            )
            seg = None
            for q in range(j, j + len(v)):
                b = bxs[q]
                if seg and abs(b[1] - seg[1]) < 1:
                    seg = (seg[0], seg[1], b[2], b[3])
                else:
                    if seg:
                        nd.append(seg + (enl,))
                    seg = tuple(b[:4])
            nd.append(seg + (enl,))
        fx = next(n for n in nd if n[4]) if arm != "A" else None
        if (
            fx is None
        ):  # COC: crop around the same needle (first enlarged one in the halfway panel)
            q = ixs.index(it["text"].find(next(v for v in vals if v in low)))
            fx = tuple(bxs[q][:2]) + tuple(
                bxs[q + 6][2:]
            )  # crop around the first needle enlarged by Half
        cx0 = int(min(max(0, fx[0] - 40), im.shape[1] - 260))
        cy = (fx[1] + fx[3]) / 2
        cy0 = int(min(max(0, cy - 23), im.shape[0] - 46))
        CROP[arm] = (cx0, cy0, cx0 + 260, cy0 + 46)
        panels.append((G, im, nd))
    E._units = old_units
    nrow0, ncol = panels[0][0].shape
    FW, FH = TEXTW, 56 * MM
    fig = plt.figure(figsize=(FW, FH))
    CARD = "#F4F5F7"
    NEED = "#222222"
    cw, gap, x00 = 0.243, 0.008, 0.004
    xs = [x00 + k * (cw + gap) for k in range(3)]
    x4 = xs[2] + cw + gap
    w4 = 0.996 - x4

    def card(x, w):
        fig.add_artist(
            FancyBboxPatch(
                (x, 0.012),
                w,
                0.976,
                boxstyle="round,pad=0,rounding_size=0.012",
                transform=fig.transFigure,
                fc=CARD,
                ec="none",
                zorder=-5,
                mutation_aspect=FW / FH,
            )
        )

    pad = 0.012
    mw = cw - 2 * pad  # map width in figure fraction -> cell size
    mh_ = mw * (FW / FH) * nrow0 / ncol  # map height for 21 rows at the same cell size
    ch0 = mw * (FW / FH) * 46 / 260
    my1 = 0.815 - ch0 - 0.07
    my0 = my1 - mh_
    for c, ((arm, m, run, title, sub), (G, im, nd)) in enumerate(zip(cols, panels)):
        x = xs[c]
        card(x, cw)
        fig.text(
            x + cw / 2,
            0.948,
            title,
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=(ACCENT_RED if arm == "S" else INK),
        )
        fig.text(
            x + cw / 2,
            0.868,
            f"({sub})",
            ha="center",
            va="center",
            fontsize=6.8,
            color=MUTED,
        )
        # rendered crop (what the VLM receives)
        x0, y0, x1, y1 = CROP[arm]
        ch = mw * (FW / FH) * (y1 - y0) / (x1 - x0)
        ax = fig.add_axes([x + pad, 0.815 - ch, mw, ch])
        ax.imshow(
            im[y0:y1, x0:x1],
            cmap="gray",
            vmin=0,
            vmax=255,
            interpolation="nearest",
            aspect="auto",
        )
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(True)
            sp.set_color(GREY)
            sp.set_linewidth(0.5)
        for bx0, by0, bx1, by1, enl in nd:
            if x0 <= bx0 and bx1 <= x1 and y0 <= by0 and by1 <= y1:
                ax.add_patch(
                    Rectangle(
                        (bx0 - x0 - 1.5, by0 - y0 - 0.5),
                        bx1 - bx0 + 3,
                        by1 - by0 + 1,
                        fill=False,
                        lw=0.9,
                        color=(ACCENT_RED if enl else NEED),
                    )
                )
                ax.text(
                    bx1 - x0 + 4,
                    (by0 + by1) / 2 - y0,
                    "enlarged needle" if enl else "needle",
                    fontsize=6.5,
                    fontweight="bold",
                    color=(ACCENT_RED if enl else NEED),
                    ha="left",
                    va="center",
                    zorder=6,
                    bbox=dict(
                        boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.92
                    ),
                )
        ya, yb = 0.815 - ch - 0.012, my1 + 0.012
        fig.add_artist(
            FancyArrowPatch(
                (x + cw / 2, ya),
                (x + cw / 2, yb),
                transform=fig.transFigure,
                arrowstyle="-|>",
                mutation_scale=6,
                lw=0.6,
                color=MUTED,
            )
        )
        fig.text(
            x + cw / 2 + 0.006,
            (ya + yb) / 2,
            "information map",
            ha="left",
            va="center",
            fontsize=6.2,
            color=MUTED,
            style="italic",
        )
        # information map, true scale
        hx = fig.add_axes([x + pad, my0, mw, mh_])
        draw_map(hx, G)
        hx.set_xlim(0, ncol)
        hx.set_ylim(nrow0, 0)
        hx.set_xticks([])
        hx.set_yticks([])
        for sp in hx.spines.values():
            sp.set_visible(False)
        saved = nrow0 - G.shape[0]
        if saved:
            hx.add_patch(
                Rectangle(
                    (0.1, G.shape[0] + 0.25),
                    ncol - 0.2,
                    saved - 0.35,
                    fill=False,
                    ls=(0, (2.5, 1.5)),
                    lw=0.6,
                    ec=GREY,
                )
            )
            hx.text(
                ncol / 2,
                G.shape[0] + saved / 2,
                f"{saved * ncol} tokens saved",
                fontsize=7,
                color=MUTED,
                ha="center",
                va="center",
            )
        for bx0, by0, bx1, by1, enl in nd:
            r0, r1 = np.floor(by0 / 28), np.ceil(by1 / 28)
            c0, c1 = np.floor(bx0 / 28), np.ceil(bx1 / 28)
            hx.add_patch(
                Rectangle(
                    (c0, r0),
                    c1 - c0,
                    r1 - r0,
                    fill=False,
                    lw=1.0,
                    ec=(ACCENT_RED if enl else NEED),
                    zorder=5,
                )
            )
        ntok = G.shape[0] * ncol
        fig.text(
            x + cw / 2,
            my0 - 0.06,
            f"{ntok} vision tokens",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=INK,
        )
        if arm == "I":
            uval = UI
            rtxt = "recall 0.56"
        else:
            uval = json.loads((run / "uniformity.json").read_text())[f"{arm}|{item}"][
                U["metric"]
            ]
            rtxt = f"recall {rec[arm]:.2f}"
        fig.text(
            x + cw / 2,
            my0 - 0.125,
            f"{G.shape[0]} $\\times$ {ncol}  ·  {rtxt}  ·  $\\mathcal{{U}}$ = {uval:.2f}",
            ha="center",
            va="center",
            fontsize=7,
            color=MUTED,
        )
    # recall vs uniformity card
    card(x4, w4)
    fig.text(
        x4 + w4 / 2,
        0.948,
        "Recall follows uniformity",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        x4 + w4 / 2,
        0.868,
        "(equal budget, 6 px, 16K characters)",
        ha="center",
        va="center",
        fontsize=6.8,
        color=MUTED,
    )
    ax = fig.add_axes([x4 + 0.048, 0.40, w4 - 0.062, 0.40])
    ax.set_facecolor(CARD)
    STY = {
        "A": ("coc", "o"),
        "U": ("coc", "s"),
        "Z": ("coc", "v"),
        "B": ("coc", "P"),
        "R": ("R", "D"),
        "H": ("H", "^"),
        "S": ("S", "*"),
    }
    pts = [p for p in U["points"] if p["setting"] == "tab1_s6"]
    for p in pts:
        k, mk = STY[p["arm"]]
        ax.scatter(
            p["U"],
            p["recall"],
            marker=mk,
            s=(55 if mk == "*" else 20),
            color=CH[k],
            edgecolor="white",
            linewidth=0.4,
            zorder=3,
        )
    l6 = {p["arm"]: p for p in pts}
    ax.text(
        l6["R"]["U"] + 0.005,
        l6["R"]["recall"],
        "random words",
        fontsize=6.3,
        ha="left",
        va="center",
    )
    ax.text(
        l6["H"]["U"] - 0.006,
        l6["H"]["recall"],
        "half enlarged",
        fontsize=6.3,
        ha="right",
        va="center",
    )
    ax.text(
        l6["S"]["U"] - 0.008,
        l6["S"]["recall"],
        NAME,
        fontsize=6.3,
        ha="right",
        va="center",
        color=ACCENT_RED,
        fontweight="bold",
    )
    ax.text(
        l6["A"]["U"] + 0.002,
        l6["A"]["recall"] + 0.06,
        "COC",
        fontsize=6.3,
        ha="center",
        va="bottom",
        linespacing=0.95,
    )
    r = U["spearman_s6"]
    ax.text(
        0.03,
        0.98,
        f"Spearman $\\rho$ = {r['rho']:.2f}",
        transform=ax.transAxes,
        fontsize=6.3,
        va="top",
        ha="left",
    )
    ax.set_xlim(0.345, 0.49)
    ax.set_xticks([0.35, 0.40, 0.45])
    ax.set_ylim(0, 0.8)
    ax.tick_params(labelsize=6.3)
    ax.set_xlabel("entropy uniformity $\\mathcal{U}$", labelpad=1, fontsize=7)
    ax.set_ylabel("needle recall (5 VLMs)", labelpad=1, fontsize=7)
    # legend: colour scale and needle outlines
    map_colorbar(fig, [x4 + 0.02, 0.165, w4 - 0.04, 0.025], label="", fontsize=6)
    fig.text(
        x4 + w4 / 2,
        0.225,
        "normalized information load (0–1)",
        ha="center",
        va="center",
        fontsize=6.3,
        color=MUTED,
    )
    lx = x4 + 0.02
    ly = 0.055
    for k, (col, lab) in enumerate(((NEED, "needle"), (ACCENT_RED, "enlarged needle"))):
        xx = lx + k * 0.085
        fig.add_artist(
            Rectangle(
                (xx, ly - 0.012),
                0.014,
                0.024,
                transform=fig.transFigure,
                fill=False,
                ec=col,
                lw=1.0,
            )
        )
        fig.text(xx + 0.019, ly, lab, fontsize=6.3, va="center", color=INK)
    fig.savefig(FIG / f"{out}.pdf", bbox_inches=None)
    fig.savefig(FIG / f"{out}.png", dpi=300, bbox_inches=None)
    plt.close(fig)


# ---------------------------------------------------------------- length scaling
R5 = [r for r in N["reader_names"] if r != "claude-sonnet-5.5"]


def b5(L, arm):
    v = [N["length_scaling"][f"{L}|{r}"][f"billed_{arm}"] for r in R5]
    v = [x for x in v if x]
    return sum(v) / len(v)


def m5(L, arm):
    return sum(N["length_scaling"][f"{L}|{r}"][arm] for r in R5) / len(
        R5
    )  # fixed 5-reader mean (review RM-7)


def scaling():
    Ls = ["32k", "64k", "128k"]
    xs = [32, 64, 128]
    ls = N["length_scaling"]
    readers = [k for k in N["reader_names"]]
    fig, (a1, a2) = plt.subplots(
        1,
        2,
        figsize=(3.3, 1.55),
        gridspec_kw=dict(wspace=0.45, left=0.13, right=0.98, bottom=0.25, top=0.8),
    )
    for ax in (a1, a2):
        style(ax)
    for arm in "AS":
        for rd in readers:
            a1.plot(
                xs,
                [ls[f"{L}|{rd}"][arm] for L in Ls],
                color=C[arm],
                lw=0.6,
                alpha=0.35,
                ls=LS[arm],
            )
        a1.plot(
            xs,
            [m5(L, arm) for L in Ls],
            color=C[arm],
            marker=MK[arm],
            ls=LS[arm],
            label=LAB[arm],
            mfc=("white" if arm == "A" else C[arm]),
        )
    a1.set_ylim(0, 1.0)
    a1.set_ylabel("needle recall")
    a1.text(0.02, 0.97, "(a)", transform=a1.transAxes, va="top", fontsize=7.5)
    for arm in "AST":
        a2.plot(
            xs,
            [b5(L, arm) / 1000 for L in Ls],
            color=C[arm],
            marker=MK[arm],
            ls=LS[arm],
            label=LAB[arm],
            mfc=("white" if arm == "A" else C[arm]),
        )
    a2.set_yscale("log")
    a2.set_yticks([1.5, 3, 6, 12, 25])
    a2.set_yticklabels(["1.5", "3", "6", "12", "25"])
    a2.minorticks_off()
    a2.set_ylabel("billed prompt tokens (K)")
    a2.text(0.02, 0.97, "(b)", transform=a2.transAxes, va="top", fontsize=7.5)
    for ax in (a1, a2):
        ax.set_xscale("log", base=2)
        ax.set_xticks(xs)
        ax.set_xticklabels(["32K", "64K", "128K"])
        ax.set_xlabel("characters")
    h, l = a2.get_legend_handles_labels()
    fig.legend(
        h,
        l,
        frameon=False,
        loc="upper center",
        ncol=3,
        fontsize=6,
        handlelength=1.8,
        bbox_to_anchor=(0.55, 1.0),
    )
    fig.savefig(FIG / "scaling.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- density sweep + routing frontier
def density():
    d = N["density_sweep"]
    ks = [1, 4, 16, 64, 128, 256]
    R = N["routing"]
    fig, axs = plt.subplots(
        1,
        3,
        figsize=(6.9, 1.75),
        gridspec_kw=dict(wspace=0.32, left=0.06, right=0.99, bottom=0.22, top=0.88),
    )
    for ax in axs:
        style(ax)
    for arm in "ASKX":
        axs[0].plot(
            ks,
            [sum(d[str(k)]["per_reader"][r][arm] for r in R5) / len(R5) for k in ks],
            color=C[arm],
            marker=MK[arm],
            ls=LS[arm],
            label=LAB[arm],
            mfc=("white" if arm == "A" else C[arm]),
        )
        axs[1].plot(
            ks,
            [d[str(k)][f"billed_{arm}"] / 1000 for k in ks],
            color=C[arm],
            marker=MK[arm],
            ls=LS[arm],
            mfc=("white" if arm == "A" else C[arm]),
        )
    for ax in axs[:2]:
        ax.set_xscale("log", base=2)
        ax.set_xticks(ks)
        ax.set_xticklabels([str(k) for k in ks])
        ax.set_xlabel("hazardous strings per 32K-char document (k)")
    axs[0].set_ylabel("needle recall")
    axs[0].set_ylim(0, 1.05)
    axs[0].set_title("(a) recall vs. hazard density", fontsize=7.5, pad=2)
    axs[1].set_ylabel("billed prompt tokens (K)")
    axs[1].set_title("(b) cost vs. hazard density", fontsize=7.5, pad=2)
    h, l = axs[0].get_legend_handles_labels()
    axs[1].legend(h, l, frameon=False, loc="upper left", fontsize=6)
    fx = [f["X"] for f in R["frontier"]]
    fk = [f["K"] for f in R["frontier"]]
    axs[2].plot(
        [p[1] for p in fk],
        [p[0] for p in fk],
        color=C["K"],
        marker=MK["K"],
        ls="-",
        label="route COC+anchor / text",
    )
    axs[2].plot(
        [p[1] for p in fx],
        [p[0] for p in fx],
        color=C["X"],
        marker=MK["X"],
        ls="-",
        label="route ours+anchors / text",
    )
    axs[2].scatter(
        [1.0], [R["mean"]["T"][0]], color=C["T"], marker=MK["T"], s=30, zorder=5
    )
    axs[2].annotate(
        "plain text",
        (1.0, R["mean"]["T"][0]),
        xytext=(0.86, 0.9),
        textcoords="data",
        fontsize=6,
        color=MUTED,
        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5),
    )
    axs[2].set_xlabel("cost relative to plain text")
    axs[2].set_ylabel("needle recall")
    axs[2].set_title("(c) density-aware routing frontier", fontsize=7.5, pad=2)
    axs[2].legend(frameon=False, loc="lower right", fontsize=6)
    fig.savefig(FIG / "density.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- appendix: short-context phase diagram (E2)
def phase():
    sw = N["sweep_short"]
    runs = [("sw_s5", 21.1), ("sw_s6", 14.0), ("sw_s8", 10.7), ("sw_s10", 7.8)]
    readers = list(N["reader_names"])
    fig, ax = plt.subplots(figsize=(3.3, 1.7))
    style(ax)
    fig.subplots_adjust(left=0.13, right=0.62, bottom=0.24, top=0.95)
    cols = ["#1F8FAE", "#E8685B", "#A83E35", "#7F8A96", "#3B3B3B", "#56B9CF"]
    mks = ["o", "s", "D", "^", "v", "P"]
    for rd, c, m in zip(readers, cols, mks):
        ys = [
            sw.get(f"{r}|{rd}", {}).get("diffs", {}).get("M-A:ids", [None])[0]
            for r, _ in runs
        ]
        ax.plot(
            [x for _, x in runs],
            ys,
            color=c,
            marker=m,
            label=N["reader_names"][rd],
            lw=1.0,
        )
    ax.axhline(0, color=MUTED, lw=0.6)
    ax.set_xlabel("characters per vision token (density)")
    ax.set_ylabel("$\\Delta$ exact-match (EquiPix $-$ COC)")
    ax.legend(frameon=False, fontsize=5.8, loc="center left", bbox_to_anchor=(1.0, 0.5))
    fig.savefig(FIG / "phase.pdf")
    plt.close(fig)


def thumbs():
    """two crops of the same 32K document (uniform vs allocated) for the method figure"""
    import make_items as M

    run = EXP / "rlong_c32k_single_3"
    it = {i["item"]: i for i in json.loads((run / "gt.json").read_text())["items"]}[1]
    man = {
        (m["item"], m["arm"]): m
        for m in json.loads((run / "manifest.json").read_text())
    }
    ma, ms = man[(1, "A")], man[(1, "S")]
    gold = it["answers"][0]
    M.REAL = False
    a = needle_crop(
        run / "img" / f"{ma['name']}.png",
        it["text"],
        M.units_uniform(it["text"], 6),
        0,
        gold,
        width=300,
        lines_ctx=4,
    )
    M.STRICT = True
    b = needle_crop(
        run / "img" / f"{ms['name']}.png",
        it["text"],
        M.units_mixed(it["text"], ms["s_lo"], ms["s_hi"]),
        ms["extra"],
        gold,
        width=300,
        lines_ctx=4,
    )
    M.STRICT = False
    a.save(FIG / "thumb_uniform.png")
    b.save(FIG / "thumb_alloc.png")
    return a.size, b.size


def examples():
    """appendix: one RULER item rendered uniformly (A), with boxed needle (B) and allocated (S); one reader's answers"""
    import make_items as M

    run = EXP / "rv2_box_s6_single_3"
    gt = {i["item"]: i for i in json.loads((run / "gt.json").read_text())["items"]}
    man = {
        (m["item"], m["arm"]): m
        for m in json.loads((run / "manifest.json").read_text())
    }
    pred = json.loads((run / "pred_or_qwen3-vl-235b-a22b-instruct.json").read_text())
    ans = lambda it, a: (
        pred.get(man[(it, a)]["name"] + ".png", {}).get("ids") or ["(none)"]
    )[0]
    ok = lambda it, a: ans(it, a).lower() == gt[it]["answers"][0].lower()
    item = next(
        i for i in sorted(gt) if not ok(i, "A") and not ok(i, "B") and ok(i, "S")
    )
    it = gt[item]
    gold = it["answers"][0]
    M.REAL = False
    crops = [
        needle_crop(
            run / "img" / f"{man[(item, 'A')]['name']}.png",
            it["text"],
            M.units_uniform(it["text"], 6),
            0,
            gold,
            width=520,
            lines_ctx=3,
        )
    ]
    M.STRICT = True
    crops.append(
        needle_crop(
            run / "img" / f"{man[(item, 'B')]['name']}.png",
            it["text"],
            M.units_mixed(it["text"], 6, 6),
            0,
            gold,
            width=520,
            lines_ctx=3,
        )
    )
    ms = man[(item, "S")]
    crops.append(
        needle_crop(
            run / "img" / f"{ms['name']}.png",
            it["text"],
            M.units_mixed(it["text"], ms["s_lo"], ms["s_hi"]),
            ms["extra"],
            gold,
            width=520,
            lines_ctx=3,
        )
    )
    M.STRICT = False
    labs = [
        ("A", "COC, 6 px"),
        ("B", "box, not enlarged"),
        ("S", f"EquiPix ({ms['s_lo']}/{ms['s_hi']} px)"),
    ]
    fig, axs = plt.subplots(
        3,
        1,
        figsize=(6.9, 3.3),
        gridspec_kw=dict(hspace=0.55, left=0.01, right=0.99, top=0.93, bottom=0.02),
    )
    for ax, im, (arm, lab) in zip(axs, crops, labs):
        ax.imshow(
            im, cmap="gray", vmin=0, vmax=255, interpolation="nearest", aspect="equal"
        )
        ax.set_xticks([])
        ax.set_yticks([])
        a = ans(item, arm)
        good = ok(item, arm)
        ax.set_title(
            f"{arm}: {lab}   Qwen3-VL answer: {a}  ({'correct' if good else 'wrong'})",
            fontsize=7,
            loc="left",
            pad=2,
            color=(C["K"] if good else C["X"]),
        )
    fig.suptitle(f"gold: {gold}", fontsize=7, x=0.01, ha="left")
    fig.savefig(FIG / "examples.pdf")
    plt.close(fig)
    return item, gold, [ans(item, a) for a in "ABS"]


def why():
    """Why allocation works: (a) exact copy given the needle was found vs glyph size, by string predictability (esz study);
    (b) wrong hex characters per right-length UUID answer, uniform vs allocated (fabrication vs reading).
    """
    W = json.loads((EXP / "analysis_why.json").read_text())
    E = W["esz"]
    An = W["anatomy"]
    fig, (a1, a2) = plt.subplots(
        1,
        2,
        figsize=(3.3, 1.75),
        gridspec_kw=dict(wspace=0.45, left=0.13, right=0.99, bottom=0.22, top=0.72),
    )
    for ax in (a1, a2):
        style(ax)
    col = dict(E=CATEGORICAL[0], W=CATEGORICAL_EXTENDED[6], H=CATEGORICAL[3])
    lab = dict(E="English phrase", W="random words", H="random hex")
    mk = dict(E="o", W="s", H="D")
    PR = E["per_reader_found_5to10"]
    rds = [
        ("gemini-3.5-flash-lite", "Gemini"),
        ("gpt-6-luna", "GPT"),
        ("llama-4-maverick", "Llama"),
    ]
    for j, t in enumerate("EWH"):
        xs = [i + (j - 1) * 0.27 for i in range(len(rds))]
        v = [PR[f"{rd}|{t}"]["exact"] for rd, _ in rds]
        a1.bar(
            xs,
            [x[0] for x in v],
            width=0.25,
            color=col[t],
            label=lab[t],
            yerr=[[x[0] - x[1] for x in v], [x[2] - x[0] for x in v]],
            error_kw=dict(lw=0.5, capsize=1),
        )
    a1.set_xticks(range(len(rds)))
    a1.set_xticklabels([n for _, n in rds])
    a1.set_ylabel("exact copy rate")
    a1.set_ylim(0, 1)
    a1.legend(
        frameon=False,
        fontsize=5.5,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.13),
        ncol=3,
        handlelength=1.2,
        columnspacing=0.8,
        borderaxespad=0,
    )
    a1.set_title("(a) copy given found, 5-10 px", fontsize=6.5, pad=2)
    bins = ["0", "1-7", "8+"]
    for k, (arm, c) in enumerate((("A", C["A"]), ("S", C["S"]))):
        v = An[arm]
        ys = [v["exact"], v["few_1_7"], v["many_8plus"]]
        a2.bar(
            [i + (k - 0.5) * 0.38 for i in range(3)],
            ys,
            width=0.36,
            color=c,
            label=f"{LAB[arm]}: hex {100*v['hex_acc']:.0f}%, hyphen {100*v['hyphen_acc']:.0f}%",
        )
    a2.set_xticks(range(3))
    a2.set_xticklabels(bins)
    a2.set_xlabel("wrong hex chars (of 32)")
    a2.set_ylabel("share of answers")
    a2.set_ylim(0, 0.75)
    a2.legend(
        frameon=False,
        fontsize=5,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.13),
        ncol=1,
        handlelength=1,
        borderaxespad=0,
    )
    a2.set_title("(b) single UUID, 5-6 px budgets", fontsize=6.5, pad=2)
    fig.savefig(FIG / "why.pdf")
    plt.close(fig)


if __name__ == "__main__":
    teaser()
    scaling()
    density()
    phase()
    print("thumbs", thumbs())
    print("examples", examples())
    why()
    print("ok")


# ---------------------------------------------------------------- pipeline thumbnails (method figure)
def thumbs_v2():
    """(1) a text snippet coloured by residual entropy h_i; (2) information-map strips of the same page region under
    COC and EquiPix (item 22 of rbx_s6_multikey_1, the teaser document)."""
    import numpy as np, re, make_items as M, entropy_map as E
    from matplotlib.colors import LinearSegmentedColormap
    from PIL import ImageDraw, ImageFont

    cmap = plt.get_cmap("Reds")  # heatmap asset (assets/figures/heatmap): cmap="Reds"
    run = EXP / "rbx_s6_multivalue"
    item = 14  # the teaser document
    it = next(
        i
        for i in json.loads((run / "gt.json").read_text())["items"]
        if i["item"] == item
    )
    mb = {
        m["arm"]: m
        for m in json.loads((run / "manifest.json").read_text())
        if m["item"] == item
    }
    h = E.surprisal(it["text"])
    v = re.findall(r"is: (\d{7})\.", it["text"])[2]
    k = it["text"].find(v)
    a0 = it["text"].rfind(" ", 0, k - 52) + 1
    snip = it["text"][a0 : k + 30]
    hs = h[a0 : k + 30]
    f = ImageFont.truetype(M.FONT_PATH, 30)
    cw = f.getlength("M")
    W = int(cw * 44) + 20
    lines, cur = [], 0
    while cur < len(snip):
        lines.append((cur, snip[cur : cur + 44]))
        cur += 44
    im = Image.new("RGB", (W, 44 * len(lines) + 10), "white")
    d = ImageDraw.Draw(im)
    for li, (o, t) in enumerate(lines):
        for j, c in enumerate(t):
            col = tuple(int(255 * x) for x in cmap(min(1.0, hs[o + j] / 6.0))[:3])
            d.rectangle(
                [10 + j * cw, 6 + li * 44, 10 + (j + 1) * cw - 1, 6 + li * 44 + 38],
                fill=col,
            )
            d.text((10 + j * cw, 8 + li * 44), c, font=f, fill=(20, 20, 20))
    im.save(FIG / "thumb_entropy.png")
    out = []
    for arm, name in (
        ("A", "thumb_map_coc"),
        ("S", "thumb_map_ours"),
    ):  # same style and size as the teaser maps
        M.STRICT = arm == "S"
        G = page_map(it["text"], arm, mb[arm])
        M.STRICT = False
        f2 = plt.figure(figsize=(34.5 * MM, 14 * MM))
        ax = f2.add_axes([0, 0, 1, 1])
        draw_map(ax, G)
        ax.set_xlim(0, G.shape[1])
        ax.set_ylim(G.shape[0], 0)
        ax.axis("off")
        f2.savefig(FIG / f"{name}.pdf", bbox_inches=None, pad_inches=0)
        plt.close(f2)
        out.append(G.shape)
    return out


# ---------------------------------------------------------------- needle load vs recall
def needle_load():
    """(a) recall of each needle vs the information load of the window around it, binned; all renderings vs COC only.
    (b) Spearman rho between needle load and recall per subset."""
    import numpy as np

    D = json.loads((EXP / "analysis_needle_load.json").read_text())
    fig, (a1, a2) = plt.subplots(
        1,
        2,
        figsize=(3.3, 1.55),
        gridspec_kw=dict(
            wspace=0.95,
            left=0.14,
            right=0.97,
            bottom=0.25,
            top=0.88,
            width_ratios=[1.15, 1],
        ),
    )
    for ax in (a1, a2):
        style(ax)
    for key, col, ls, lab in (
        ("binned_all", CH["S"], "-", "all renderings"),
        ("binned_coc", CH["coc"], "--", "COC only"),
    ):
        b = D[key]
        x = [v["mid"] for v in b]
        y = [v["mean"] for v in b]
        a1.fill_between(
            x,
            [v["ci"][0] for v in b],
            [v["ci"][1] for v in b],
            color=col,
            alpha=0.15,
            lw=0,
        )
        a1.plot(x, y, color=col, ls=ls, marker="o", ms=2.5, label=lab)
    a1.set_xlabel("needle load (bits per vision token)", labelpad=1)
    a1.set_ylabel("recall (5 VLMs)", labelpad=1)
    a1.set_ylim(0, 0.85)
    a1.legend(frameon=False, fontsize=5.8, loc="upper right", handlelength=1.6)
    a1.set_title("(a) hotter needles are read worse", fontsize=6.5, pad=2)
    names = list(D["subsets"])
    short = {
        "RULER 16K": "RULER 16K",
        "RULER 32K-128K": "RULER 32-128K",
        "RULER 8-10 px": "RULER 8-10 px",
        "half": "half",
        "box": "box runs",
        "natural, flagged": "natural, flagged",
        "natural, det.-indep.": "natural, indep.",
    }
    ys = np.arange(len(names))[::-1]
    a2.barh(
        ys + 0.18,
        [D["subsets"][n]["all"]["rho"] for n in names],
        height=0.34,
        color=CH["S"],
        label="all",
    )
    a2.barh(
        ys - 0.18,
        [D["subsets"][n]["coc"]["rho"] if D["subsets"][n]["coc"] else 0 for n in names],
        height=0.34,
        color=CH["coc"],
        label="COC",
    )
    a2.set_yticks(ys)
    a2.set_yticklabels([short[n] for n in names], fontsize=5.6)
    a2.axvline(0, color=MUTED, lw=0.5)
    a2.set_xlim(-0.75, 0.05)
    a2.set_xticks([-0.6, -0.3, 0])
    a2.set_xlabel("Spearman $\\rho$", labelpad=1)
    a2.legend(frameon=False, fontsize=5.5, loc="lower left", handlelength=1)
    a2.set_title("(b) per subset", fontsize=6.5, pad=2)
    fig.savefig(FIG / "needle_load.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- natural document: information map around a target
def natural_map(item=24):
    """niq2_s6 item: crops around the target under COC and EquiPix with the vision-token information map (same style as
    the teaser) drawn under the glyphs, plus the target's load and five-reader recall.
    """
    import numpy as np, re, make_items as M, entropy_map as E
    from stats_pooled import merged

    run = EXP / "niq2_s6"
    it = next(
        i
        for i in json.loads((run / "gt.json").read_text())["items"]
        if i["item"] == item
    )
    man = {
        m["arm"]: m
        for m in json.loads((run / "manifest.json").read_text())
        if m["item"] == item
    }
    ph = re.search(r'immediately after the words "(.*?)"\?', it["prompt"]).group(1)
    k = it["text"].find(ph) + len(ph) + 1
    v = it["answers"][0]
    dd = merged(["niq2_s6"])["niq2_s6"]
    rec = {
        a: np.mean(
            [dd[r][item][a]["recall"] for r in dd if item in dd[r] and a in dd[r][item]]
        )
        for a in "AS"
    }
    U = json.loads((run / "uniformity.json").read_text())
    fig, axs = plt.subplots(
        2,
        1,
        figsize=(COLW, 36 * MM),
        gridspec_kw=dict(hspace=0.45, left=0.01, right=0.99, top=0.9, bottom=0.2),
    )
    NC, NR = 15, 2
    for ax, arm in zip(axs, "AS"):
        M.STRICT = arm == "S"
        G = page_map(it["text"], arm, man[arm])
        bx, ix, _ = E.cells(it["text"], arm, man[arm], 6)
        M.STRICT = False
        ix = list(ix)
        j0, j1 = ix.index(k), ix.index(k + len(v) - 1)
        x0, y0 = bx[j0][:2]
        x1, y1 = bx[j1][2:]
        c0 = int(max(0, min(G.shape[1] - NC, x0 // 28 - 5)))
        r0 = int(max(0, min(G.shape[0] - NR, ((y0 + y1) / 2 - 14) // 28)))
        img = (
            np.array(
                Image.open(run / "img" / f"{man[arm]['name']}.png").convert("L"), float
            )
            / 255
        )
        crop = np.ones((NR * 28, NC * 28))
        part = img[r0 * 28 : (r0 + NR) * 28, c0 * 28 : (c0 + NC) * 28]
        crop[: part.shape[0], : part.shape[1]] = (
            part  # pad the last partial token row with white
        )
        draw_map(ax, G[r0 : r0 + NR, c0 : c0 + NC])
        ink = np.zeros(crop.shape + (4,))
        ink[..., 3] = (1 - crop) ** 0.8  # glyphs in black on top of the map
        ax.imshow(ink, extent=(0, NC, NR, 0), interpolation="nearest", zorder=2)
        ax.add_patch(
            plt.Rectangle(
                (x0 / 28 - c0 - 0.05, y0 / 28 - r0 - 0.03),
                (x1 - x0) / 28 + 0.1,
                (y1 - y0) / 28 + 0.06,
                fill=False,
                lw=0.9,
                color=BLACK,
                zorder=3,
            )
        )
        ax.set_xlim(0, NC)
        ax.set_ylim(NR, 0)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        nl = U[f"{arm}|{item}"]["needle_load"]
        tl = list(nl.values())[0] if nl else float("nan")
        ax.set_title(
            f"{'COC (6 px)' if arm == 'A' else NAME + ' (5 / 12 px)'}:  target load {tl:.0f} bits/vision token,  recall {rec[arm]:.1f}",
            fontsize=6.5,
            pad=2,
            loc="left",
        )
    map_colorbar(fig, [0.03, 0.06, 0.32, 0.03], fontsize=6)
    fig.savefig(FIG / "natural_map.pdf")
    plt.close(fig)
    return v, rec
