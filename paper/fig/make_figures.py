"""Figures for the paper. All numbers come from paper/data/numbers.json (built by extract_numbers.py);
teaser crops come from the rendered images of thoughts/exp/real/rlong_c32k_single_3 (item 1).
usage: python3 paper/fig/make_figures.py   -> paper/fig/*.pdf"""
import json, re, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]; FIG = Path(__file__).resolve().parent
EXP = ROOT / "thoughts" / "exp" / "real"; sys.path.insert(0, str(EXP))
N = json.loads((ROOT / "paper" / "data" / "numbers.json").read_text())

# validated categorical set (dataviz validator, --pairs all PASS): K teal, S coral, X dark coral; A = neutral reference
C = dict(A="#7F8A96", K="#1F8FAE", S="#E8685B", X="#A83E35", T="#3B3B3B")
MK = dict(A="o", K="s", S="D", X="^", T="*")
LS = dict(A="--", K="-", S="-", X="-", T=":")
NAME = "EquiPix"
LAB = dict(A="COC", K="COC+anchor", S="EquiPix (ours)", X="EquiPix+anchor", T="Plain text")
INK, MUTED, GRID = "#2B2B2B", "#6B6B6B", "#E3E7EC"
LIGHT = dict(aqua="#BFE6EA", peach="#F7D8B8", mist="#D9E2EB", warm="#F2F2F2", salmon="#F6A69A")
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
                     "font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 8.5, "legend.fontsize": 7.5,
                     "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": INK, "text.color": INK,
                     "lines.linewidth": 1.4, "lines.markersize": 4, "pdf.fonttype": 42, "axes.spines.top": False,
                     "axes.spines.right": False})

def style(ax):
    ax.grid(True, color=GRID, lw=0.5); ax.set_axisbelow(True)

# ---------------------------------------------------------------- teaser
def needle_crop(img_path, text, units, lead, answer, width=330, lines_ctx=5):
    import make_items as M
    lines = M.layout(units)
    heights = [max(sum(M.font(s).getmetrics()) for _, _, s in ln) + 1 +
               (lead if all(s == min(x for _, x in units) for _, _, s in ln) else 0) for ln in lines]
    flat, y = "", M.MARGIN; pos = []
    for ln, h in zip(lines, heights):
        pos.append((len(flat), y, h)); flat += "".join(t for _, t, _ in ln); y += h
    i = flat.find(answer); li = max(n for n, (o, _, _) in enumerate(pos) if o <= i)
    # x of the answer inside its line
    ln = lines[li]; acc = pos[li][0]; x0 = None
    for x, t, s in ln:
        if acc <= i < acc + len(t): x0 = x; break
        acc += len(t)
    im = Image.open(img_path).convert("L")
    top = pos[max(0, li - lines_ctx)][1]; bot = pos[min(len(pos) - 1, li + lines_ctx)][1] + pos[min(len(pos) - 1, li + lines_ctx)][2]
    left = max(0, min(im.width - width, x0 - 40))
    return im.crop((left, top, left + width, bot))

def teaser_old():
    import make_items as M
    run = EXP / "rlong_c32k_single_3"; gt = {it["item"]: it for it in json.loads((run / "gt.json").read_text())["items"]}
    man = {(m["item"], m["arm"]): m for m in json.loads((run / "manifest.json").read_text())}
    it = gt[1]; gold = it["answers"][0]
    pa = json.loads((run / "pred_or_claude-sonnet-5.5.json").read_text())
    ma, ms = man[(1, "A")], man[(1, "S")]
    ans_a, ans_s = pa[ma["name"] + ".png"]["ids"][0], pa[ms["name"] + ".png"]["ids"][0]
    M.REAL = False
    crop_a = needle_crop(run / "img" / f"{ma['name']}.png", it["text"], M.units_uniform(it["text"], 6), 0, gold)
    zoom_a = needle_crop(run / "img" / f"{ma['name']}.png", it["text"], M.units_uniform(it["text"], 6), 0, gold, width=300, lines_ctx=0)
    M.STRICT = True
    crop_s = needle_crop(run / "img" / f"{ms['name']}.png", it["text"], M.units_mixed(it["text"], ms["s_lo"], ms["s_hi"]), ms["extra"], gold)
    zoom_s = needle_crop(run / "img" / f"{ms['name']}.png", it["text"], M.units_mixed(it["text"], ms["s_lo"], ms["s_hi"]), ms["extra"], gold, width=300, lines_ctx=0)
    M.STRICT = False
    fig = plt.figure(figsize=(6.9, 2.45))
    gs = fig.add_gridspec(3, 3, width_ratios=[1.0, 1.0, 0.8], height_ratios=[1, 0.3, 0.42], wspace=0.2, hspace=0.12,
                          left=0.01, right=0.99, top=0.91, bottom=0.15)
    for col, (crop, zoom, title, ans, ok, arm) in enumerate([(crop_a, zoom_a, "Uniform rendering (6 px everywhere)", ans_a, False, "A"),
                                                       (crop_s, zoom_s, "Hazard-aware rendering (ours, same budget)", ans_s, True, "S")]):
        ax = fig.add_subplot(gs[0, col]); ax.imshow(crop, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values(): sp.set_visible(True); sp.set_color(C[arm]); sp.set_linewidth(1.2)
        ax.set_title(title, fontsize=8, color=INK, pad=3)
        zx = fig.add_subplot(gs[1, col]); zx.imshow(zoom, cmap="gray", vmin=0, vmax=255, interpolation="nearest", aspect="equal")
        zx.set_xticks([]); zx.set_yticks([])
        for sp in zx.spines.values(): sp.set_visible(True); sp.set_color(C[arm]); sp.set_linewidth(0.8); sp.set_linestyle(":")
        tx = fig.add_subplot(gs[2, col]); tx.axis("off")
        tx.text(0.0, 0.78, f"Q: the special magic uuid for '{it['query']}'?", fontsize=6.3, color=MUTED, transform=tx.transAxes)
        # answer with wrong characters marked
        x = 0.0; tx.text(x, 0.42, "A:", fontsize=6.6, family="monospace", transform=tx.transAxes); x += 0.05
        for a, g in zip(ans, gold):
            tx.text(x, 0.42, a, fontsize=6.6, family="monospace", transform=tx.transAxes,
                    color=(C["X"] if a != g else INK), fontweight=("bold" if a != g else "normal")); x += 0.0255
        nwrong = sum(a != g for a, g in zip(ans, gold))
        tx.text(0.0, 0.02, "correct" if ok else f"{nwrong} characters wrong, well-formed, no abstention (silent error)",
                fontsize=6.3, transform=tx.transAxes, color=(C["K"] if ok else C["X"]))
    ax = fig.add_subplot(gs[:, 2]); style(ax)
    Ls = ["32k", "64k", "128k"]; xs = [32, 64, 128]
    for arm in "AS":
        ys = [m5(L, arm) for L in Ls]
        ax.plot(xs, ys, color=C[arm], ls=LS[arm], marker=MK[arm], label=LAB[arm], mfc=("white" if arm == "A" else C[arm]))
    ax.set_xscale("log", base=2); ax.set_xticks(xs); ax.set_xticklabels(["32K", "64K", "128K"])
    ax.set_ylim(0, 0.8); ax.set_xlabel("context length (characters)"); ax.set_ylabel("needle recall (5 VLMs)")
    ax.legend(loc="center left", frameon=False, bbox_to_anchor=(0.02, 0.42), handlelength=1.8)
    ax.set_title("Equal vision-token budget", fontsize=7.5, pad=3)
    fig.savefig(FIG / "teaser.pdf"); plt.close(fig)
    return ans_a, ans_s, gold


# ---------------------------------------------------------------- teaser (v2): information maps + recall vs uniformity
CH = dict(coc="#7F8A96", R="#1F8FAE", H="#D9A23A", S="#E8685B")
def load_raster(text, arm, m, size, n=48):
    """per-pixel information load: every glyph cell painted with the load (bits / vision token) of the n-character
    reading-order window centred on it; NaN where nothing is drawn"""
    import numpy as np, entropy_map as E
    h, a = E.char_load(text, arm, m, size); w = E.window_load(h, a, n)
    lc = np.concatenate([np.full(n // 2, w[0]), w, np.full(len(text) - len(w) - n // 2, w[-1])])
    bx, ix, (Wd, Hd) = E.cells(text, arm, m, size); R = np.full((Hd, Wd), np.nan)
    for (x0, y0, x1, y1), i in zip(bx, ix): R[int(y0):int(np.ceil(y1)), int(x0):int(np.ceil(x1))] = lc[i]
    return R

def teaser():
    import numpy as np, make_items as M
    from matplotlib.colors import LinearSegmentedColormap
    U = json.loads((EXP / "analysis_uniformity.json").read_text())
    run_b, run_h = EXP / "rbx_s6_multikey_1", EXP / "rhalf_s6_multikey_1"; item = 22
    it = next(i for i in json.loads((run_b / "gt.json").read_text())["items"] if i["item"] == item)
    mb = {m["arm"]: m for m in json.loads((run_b / "manifest.json").read_text()) if m["item"] == item}
    mh = next(m for m in json.loads((run_h / "manifest.json").read_text()) if m["item"] == item)
    cols = [("A", mb["A"], run_b, "COC (typical)", "all text at 6 px"), ("H", mh, run_h, "Half enlarged", "2 of 4 needles at 12 px, prose 5 px"),
            ("S", mb["S"], run_b, f"{NAME} (ours)", "all 4 needles at 12 px, prose 5 px")]
    cmap = LinearSegmentedColormap.from_list("load", ["#FBF1EC", "#F2A08F", "#E8685B", "#A83E35", "#4A1410"])
    rasters, crops = [], []
    for arm, m, run, *_ in cols:
        M.STRICT = arm in "SH"; M.ORACLE = set(mh["enlarged"]) if arm == "H" else None
        Rr = load_raster(it["text"], arm, m, 6); rasters.append(Rr / np.nanmean(Rr)); M.STRICT = False; M.ORACLE = None
        im = np.array(Image.open(Path(str(run).replace("rbx_", "rbase_")) / "img" / f"{m['name']}.png").convert("L"))
        box = {"A": (330, 538, 590, 584), "H": (100, 370, 360, 416), "S": (127, 378, 387, 424)}[arm]
        crops.append((im, box))
    from stats_pooled import merged  # recall on the same 50 documents (multi-key + multi-value, 6 px) for all three columns
    import statistics as St
    dd = merged([f"rbx_s6_{t}+rhalf_s6_{t}" for t in ("multikey_1", "multivalue")])
    rec = {a: St.mean(v[a]["recall"] for run in dd.values() for rows in run.values() for v in rows.values() if a in v) for a in "AHS"}
    vmin, vmax = 0.6, 3.0
    fig = plt.figure(figsize=(6.9, 2.4))
    gs = fig.add_gridspec(2, 4, width_ratios=[1, 1, 1, 1.12], height_ratios=[0.36, 1], wspace=0.12, hspace=0.16,
                          left=0.005, right=0.985, top=0.9, bottom=0.15)
    from uniformity_study import N0
    import entropy_map as E
    for c, ((arm, m, run, title, sub), R, (im, box)) in enumerate(zip(cols, rasters, crops)):
        ax = fig.add_subplot(gs[0, c]); x0, y0, x1, y1 = box
        ax.imshow(im[y0:y1, x0:x1], cmap="gray", vmin=0, vmax=255, interpolation="nearest"); ax.set_xticks([]); ax.set_yticks([])
        import entropy_map as E
        M.STRICT = arm in "SH"; M.ORACLE = set(mh["enlarged"]) if arm == "H" else None
        bxs, ixs, _ = E.cells(it["text"], arm, m, 6); M.STRICT = False; M.ORACLE = None; ixs = list(ixs)
        for v in re.findall(r"is: (\d{7})\.", it["text"]):  # mark every needle inside the crop
            j = ixs.index(it["text"].find(v)); bx0, by0 = bxs[j][:2]; bx1, by1 = bxs[j + len(v) - 1][2:]
            if x0 <= bx0 and bx1 <= x1 and y0 <= by0 and by1 <= y1:
                ax.add_patch(plt.Rectangle((bx0 - x0 - 1.5, by0 - y0 - 0.5), bx1 - bx0 + 3, by1 - by0 + 1, fill=False, lw=0.7,
                                           color=(CH["S"] if (arm == "S" or (arm == "H" and v in mh["enlarged"])) else CH["R"])))
        for sp in ax.spines.values(): sp.set_visible(True); sp.set_color(CH["coc" if arm == "A" else arm]); sp.set_linewidth(1.1)
        ax.set_title(f"{title}\n", fontsize=7.6, pad=1, color=INK, fontweight="bold")
        ax.text(0.5, 1.04, sub, transform=ax.transAxes, ha="center", va="bottom", fontsize=6.2, color=MUTED)
        hx = fig.add_subplot(gs[1, c]); Hmax = max(r.shape[0] for r in rasters)
        bg = np.where(np.isnan(R), np.nan, R)
        hx.imshow(np.ones_like(R), cmap="gray", vmin=0, vmax=1, extent=(0, R.shape[1], R.shape[0], 0))
        hx.imshow(bg, cmap=cmap, vmin=vmin, vmax=vmax, interpolation="bilinear", extent=(0, R.shape[1], R.shape[0], 0))
        hx.set_xlim(0, R.shape[1]); hx.set_ylim(Hmax, 0); hx.set_xticks([]); hx.set_yticks([])
        for sp in hx.spines.values(): sp.set_visible(False)
        hx.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=0.6, ls=":", color=INK))
        st = json.loads((run / "uniformity.json").read_text())[f"{arm}|{item}"]
        hx.text(0.0, Hmax + 14, f"$\\mathcal{{U}}$ = {st[U['metric']]:.2f} (this page)   recall = {rec[arm]:.2f}",
                fontsize=6.4, va="top", color=INK, transform=hx.transData)
    # colorbar under the maps
    cax = fig.add_axes([0.03, 0.07, 0.25, 0.022]); sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin, vmax))
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal"); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=5.5, length=1.5, pad=1)
    cax.set_title("information load relative to the page mean", fontsize=5.8, pad=1.5, color=MUTED)
    # scatter: recall vs uniformity, equal-budget points
    ax = fig.add_subplot(gs[:, 3]); style(ax)
    STY = {"A": ("coc", "o", "COC"), "U": ("coc", "s", "font search"), "Z": ("coc", "v", "downsample"), "B": ("coc", "P", "box"),
           "R": ("R", "D", "random words"), "H": ("H", "^", "half"), "S": ("S", "*", NAME)}
    pts = [p for p in U["points"] if p["setting"] in ("tab1_s5", "tab1_s6")]
    for p in pts:
        k, mk, lab = STY[p["arm"]]; filled = p["setting"] == "tab1_s6"
        ax.scatter(p["U"], p["recall"], marker=mk, s=(46 if mk == "*" else 20), color=(CH[k] if filled else "white"),
                   edgecolor=CH[k], linewidth=0.9, zorder=3)
    lab6 = {p["arm"]: p for p in pts if p["setting"] == "tab1_s6"}
    ax.text(lab6["R"]["U"], lab6["R"]["recall"] + 0.035, "random\nwords", fontsize=5.8, color=INK, ha="center", va="bottom", linespacing=0.9)
    ax.text(lab6["H"]["U"] - 0.006, lab6["H"]["recall"], "half", fontsize=5.8, color=INK, ha="right", va="center")
    ax.text(lab6["S"]["U"] - 0.007, lab6["S"]["recall"] + 0.01, NAME, fontsize=5.8, color=INK, ha="right", va="center")
    ax.text(lab6["A"]["U"] + 0.004, lab6["A"]["recall"] + 0.07, "COC, font search,\ndownsample, box", fontsize=5.8, color=INK, ha="center", va="bottom", linespacing=0.9)
    r = U["spearman_eq16k"]
    ax.text(0.03, 0.97, f"Spearman $\\rho$ = {r['rho']:.2f}\n(p = {r['p']:.1g}, {r['n']} arm × budget)", transform=ax.transAxes,
            fontsize=6.3, va="top", color=INK)
    ax.scatter([], [], marker="o", color=MUTED, s=14, label="6 px budget"); ax.scatter([], [], marker="o", facecolor="white", edgecolor=MUTED, s=14, label="5 px budget")
    ax.legend(frameon=False, loc="lower right", fontsize=5.8, handletextpad=0.2, borderaxespad=0.1)
    ax.set_xlabel("entropy uniformity $\\mathcal{U}$", labelpad=1); ax.set_ylabel("needle recall (5 VLMs)", labelpad=1)
    ax.set_ylim(0, 0.8); ax.set_title("Equal vision-token budget, 16K chars", fontsize=7, pad=3)
    fig.savefig(FIG / "teaser.pdf"); plt.close(fig)

# ---------------------------------------------------------------- length scaling
R5 = [r for r in N["reader_names"] if r != "claude-sonnet-5.5"]
def b5(L, arm):
    v = [N["length_scaling"][f"{L}|{r}"][f"billed_{arm}"] for r in R5]; v = [x for x in v if x]; return sum(v) / len(v)
def m5(L, arm): return sum(N["length_scaling"][f"{L}|{r}"][arm] for r in R5) / len(R5)  # fixed 5-reader mean (review RM-7)
def scaling():
    Ls = ["32k", "64k", "128k"]; xs = [32, 64, 128]; ls = N["length_scaling"]
    readers = [k for k in N["reader_names"]]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.3, 1.55), gridspec_kw=dict(wspace=0.45, left=0.13, right=0.98, bottom=0.25, top=0.8))
    for ax in (a1, a2): style(ax)
    for arm in "AS":
        for rd in readers:
            a1.plot(xs, [ls[f"{L}|{rd}"][arm] for L in Ls], color=C[arm], lw=0.6, alpha=0.35, ls=LS[arm])
        a1.plot(xs, [m5(L, arm) for L in Ls], color=C[arm], marker=MK[arm], ls=LS[arm], label=LAB[arm],
                mfc=("white" if arm == "A" else C[arm]))
    a1.set_ylim(0, 1.0); a1.set_ylabel("needle recall"); a1.text(0.02, 0.97, "(a)", transform=a1.transAxes, va="top", fontsize=7.5)
    for arm in "AST":
        a2.plot(xs, [b5(L, arm) / 1000 for L in Ls], color=C[arm], marker=MK[arm], ls=LS[arm],
                label=LAB[arm], mfc=("white" if arm == "A" else C[arm]))
    a2.set_yscale("log"); a2.set_yticks([1.5, 3, 6, 12, 25]); a2.set_yticklabels(["1.5", "3", "6", "12", "25"])
    a2.minorticks_off(); a2.set_ylabel("billed prompt tokens (K)"); a2.text(0.02, 0.97, "(b)", transform=a2.transAxes, va="top", fontsize=7.5)
    for ax in (a1, a2):
        ax.set_xscale("log", base=2); ax.set_xticks(xs); ax.set_xticklabels(["32K", "64K", "128K"]); ax.set_xlabel("characters")
    h, l = a2.get_legend_handles_labels()
    fig.legend(h, l, frameon=False, loc="upper center", ncol=3, fontsize=6, handlelength=1.8, bbox_to_anchor=(0.55, 1.0))
    fig.savefig(FIG / "scaling.pdf"); plt.close(fig)

# ---------------------------------------------------------------- density sweep + routing frontier
def density():
    d = N["density_sweep"]; ks = [1, 4, 16, 64, 128, 256]; R = N["routing"]
    fig, axs = plt.subplots(1, 3, figsize=(6.9, 1.75), gridspec_kw=dict(wspace=0.32, left=0.06, right=0.99, bottom=0.22, top=0.88))
    for ax in axs: style(ax)
    for arm in "ASKX":
        axs[0].plot(ks, [sum(d[str(k)]["per_reader"][r][arm] for r in R5) / len(R5) for k in ks], color=C[arm], marker=MK[arm], ls=LS[arm], label=LAB[arm],
                    mfc=("white" if arm == "A" else C[arm]))
        axs[1].plot(ks, [d[str(k)][f"billed_{arm}"] / 1000 for k in ks], color=C[arm], marker=MK[arm], ls=LS[arm],
                    mfc=("white" if arm == "A" else C[arm]))
    for ax in axs[:2]:
        ax.set_xscale("log", base=2); ax.set_xticks(ks); ax.set_xticklabels([str(k) for k in ks]); ax.set_xlabel("hazardous strings per 32K-char document (k)")
    axs[0].set_ylabel("needle recall"); axs[0].set_ylim(0, 1.05); axs[0].set_title("(a) recall vs. hazard density", fontsize=7.5, pad=2)
    axs[1].set_ylabel("billed prompt tokens (K)"); axs[1].set_title("(b) cost vs. hazard density", fontsize=7.5, pad=2)
    h, l = axs[0].get_legend_handles_labels(); axs[1].legend(h, l, frameon=False, loc="upper left", fontsize=6)
    fx = [f["X"] for f in R["frontier"]]; fk = [f["K"] for f in R["frontier"]]
    axs[2].plot([p[1] for p in fk], [p[0] for p in fk], color=C["K"], marker=MK["K"], ls="-", label="route COC+anchor / text")
    axs[2].plot([p[1] for p in fx], [p[0] for p in fx], color=C["X"], marker=MK["X"], ls="-", label="route ours+anchors / text")
    axs[2].scatter([1.0], [R["mean"]["T"][0]], color=C["T"], marker=MK["T"], s=30, zorder=5)
    axs[2].annotate("plain text", (1.0, R["mean"]["T"][0]), xytext=(0.86, 0.9), textcoords="data", fontsize=6, color=MUTED,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5))
    axs[2].set_xlabel("cost relative to plain text"); axs[2].set_ylabel("needle recall")
    axs[2].set_title("(c) density-aware routing frontier", fontsize=7.5, pad=2); axs[2].legend(frameon=False, loc="lower right", fontsize=6)
    fig.savefig(FIG / "density.pdf"); plt.close(fig)

# ---------------------------------------------------------------- appendix: short-context phase diagram (E2)
def phase():
    sw = N["sweep_short"]; runs = [("sw_s5", 21.1), ("sw_s6", 14.0), ("sw_s8", 10.7), ("sw_s10", 7.8)]
    readers = list(N["reader_names"])
    fig, ax = plt.subplots(figsize=(3.3, 1.7)); style(ax); fig.subplots_adjust(left=0.13, right=0.62, bottom=0.24, top=0.95)
    cols = ["#1F8FAE", "#E8685B", "#A83E35", "#7F8A96", "#3B3B3B", "#56B9CF"]; mks = ["o", "s", "D", "^", "v", "P"]
    for rd, c, m in zip(readers, cols, mks):
        ys = [sw.get(f"{r}|{rd}", {}).get("diffs", {}).get("M-A:ids", [None])[0] for r, _ in runs]
        ax.plot([x for _, x in runs], ys, color=c, marker=m, label=N["reader_names"][rd], lw=1.0)
    ax.axhline(0, color=MUTED, lw=0.6); ax.set_xlabel("characters per vision token (density)"); ax.set_ylabel("$\\Delta$ exact-match (EquiPix $-$ COC)")
    ax.legend(frameon=False, fontsize=5.8, loc="center left", bbox_to_anchor=(1.0, 0.5))
    fig.savefig(FIG / "phase.pdf"); plt.close(fig)

def thumbs():
    """two crops of the same 32K document (uniform vs allocated) for the method figure"""
    import make_items as M
    run = EXP / "rlong_c32k_single_3"; it = {i["item"]: i for i in json.loads((run / "gt.json").read_text())["items"]}[1]
    man = {(m["item"], m["arm"]): m for m in json.loads((run / "manifest.json").read_text())}
    ma, ms = man[(1, "A")], man[(1, "S")]; gold = it["answers"][0]; M.REAL = False
    a = needle_crop(run / "img" / f"{ma['name']}.png", it["text"], M.units_uniform(it["text"], 6), 0, gold, width=300, lines_ctx=4)
    M.STRICT = True
    b = needle_crop(run / "img" / f"{ms['name']}.png", it["text"], M.units_mixed(it["text"], ms["s_lo"], ms["s_hi"]), ms["extra"], gold, width=300, lines_ctx=4)
    M.STRICT = False
    a.save(FIG / "thumb_uniform.png"); b.save(FIG / "thumb_alloc.png"); return a.size, b.size

def examples():
    """appendix: one RULER item rendered uniformly (A), with boxed needle (B) and allocated (S); one reader's answers"""
    import make_items as M
    run = EXP / "rv2_box_s6_single_3"; gt = {i["item"]: i for i in json.loads((run / "gt.json").read_text())["items"]}
    man = {(m["item"], m["arm"]): m for m in json.loads((run / "manifest.json").read_text())}
    pred = json.loads((run / "pred_or_qwen3-vl-235b-a22b-instruct.json").read_text())
    ans = lambda it, a: (pred.get(man[(it, a)]["name"] + ".png", {}).get("ids") or ["(none)"])[0]
    ok = lambda it, a: ans(it, a).lower() == gt[it]["answers"][0].lower()
    item = next(i for i in sorted(gt) if not ok(i, "A") and not ok(i, "B") and ok(i, "S"))
    it = gt[item]; gold = it["answers"][0]; M.REAL = False
    crops = [needle_crop(run / "img" / f"{man[(item, 'A')]['name']}.png", it["text"], M.units_uniform(it["text"], 6), 0, gold, width=520, lines_ctx=3)]
    M.STRICT = True
    crops.append(needle_crop(run / "img" / f"{man[(item, 'B')]['name']}.png", it["text"], M.units_mixed(it["text"], 6, 6), 0, gold, width=520, lines_ctx=3))
    ms = man[(item, "S")]
    crops.append(needle_crop(run / "img" / f"{ms['name']}.png", it["text"], M.units_mixed(it["text"], ms["s_lo"], ms["s_hi"]), ms["extra"], gold, width=520, lines_ctx=3))
    M.STRICT = False
    labs = [("A", "COC, 6 px"), ("B", "box, not enlarged"), ("S", f"EquiPix ({ms['s_lo']}/{ms['s_hi']} px)")]
    fig, axs = plt.subplots(3, 1, figsize=(6.9, 3.3), gridspec_kw=dict(hspace=0.55, left=0.01, right=0.99, top=0.93, bottom=0.02))
    for ax, im, (arm, lab) in zip(axs, crops, labs):
        ax.imshow(im, cmap="gray", vmin=0, vmax=255, interpolation="nearest", aspect="equal"); ax.set_xticks([]); ax.set_yticks([])
        a = ans(item, arm); good = ok(item, arm)
        ax.set_title(f"{arm}: {lab}   Qwen3-VL answer: {a}  ({'correct' if good else 'wrong'})", fontsize=7, loc="left", pad=2,
                     color=(C["K"] if good else C["X"]))
    fig.suptitle(f"gold: {gold}", fontsize=7, x=0.01, ha="left")
    fig.savefig(FIG / "examples.pdf"); plt.close(fig); return item, gold, [ans(item, a) for a in "ABS"]

def why():
    """Why allocation works: (a) exact copy given the needle was found vs glyph size, by string predictability (esz study);
    (b) wrong hex characters per right-length UUID answer, uniform vs allocated (fabrication vs reading)."""
    W = json.loads((EXP / "analysis_why.json").read_text()); E = W["esz"]; An = W["anatomy"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.3, 1.75), gridspec_kw=dict(wspace=0.45, left=0.13, right=0.99, bottom=0.22, top=0.72))
    for ax in (a1, a2): style(ax)
    col = dict(E="#1F8FAE", W="#56B9CF", H="#E8685B"); lab = dict(E="English phrase", W="random words", H="random hex")
    mk = dict(E="o", W="s", H="D")
    PR = E["per_reader_found_5to10"]; rds = [("gemini-3.5-flash-lite", "Gemini"), ("gpt-6-luna", "GPT"), ("llama-4-maverick", "Llama")]
    for j, t in enumerate("EWH"):
        xs = [i + (j - 1) * 0.27 for i in range(len(rds))]; v = [PR[f"{rd}|{t}"]["exact"] for rd, _ in rds]
        a1.bar(xs, [x[0] for x in v], width=0.25, color=col[t], label=lab[t],
               yerr=[[x[0] - x[1] for x in v], [x[2] - x[0] for x in v]], error_kw=dict(lw=0.5, capsize=1))
    a1.set_xticks(range(len(rds))); a1.set_xticklabels([n for _, n in rds]); a1.set_ylabel("exact copy rate"); a1.set_ylim(0, 1)
    a1.legend(frameon=False, fontsize=5.5, loc="lower center", bbox_to_anchor=(0.5, 1.13), ncol=3, handlelength=1.2, columnspacing=0.8, borderaxespad=0)
    a1.set_title("(a) copy given found, 5-10 px", fontsize=6.5, pad=2)
    bins = ["0", "1-7", "8+"]
    for k, (arm, c) in enumerate((("A", C["A"]), ("S", C["S"]))):
        v = An[arm]; ys = [v["exact"], v["few_1_7"], v["many_8plus"]]
        a2.bar([i + (k - 0.5) * 0.38 for i in range(3)], ys, width=0.36, color=c, label=f"{LAB[arm]}: hex {100*v['hex_acc']:.0f}%, hyphen {100*v['hyphen_acc']:.0f}%")
    a2.set_xticks(range(3)); a2.set_xticklabels(bins); a2.set_xlabel("wrong hex chars (of 32)"); a2.set_ylabel("share of answers")
    a2.set_ylim(0, 0.75); a2.legend(frameon=False, fontsize=5, loc="lower center", bbox_to_anchor=(0.5, 1.13), ncol=1, handlelength=1, borderaxespad=0)
    a2.set_title("(b) single UUID, 5-6 px budgets", fontsize=6.5, pad=2)
    fig.savefig(FIG / "why.pdf"); plt.close(fig)

if __name__ == "__main__":
    teaser(); scaling(); density(); phase(); print("thumbs", thumbs()); print("examples", examples()); why(); print("ok")
