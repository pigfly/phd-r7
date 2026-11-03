"""Figures for the paper. All numbers come from paper/data/numbers.json (built by extract_numbers.py);
teaser crops come from the rendered images of thoughts/exp/real/rlong_c32k_single_3 (item 1).
usage: python3 paper/fig/make_figures.py   -> paper/fig/*.pdf"""
import json, sys
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
LAB = dict(A="Uniform (A)", K="Anchors (K)", S="Ours (S)", X="Ours + anchors (X)", T="Plain text (T)")
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

def teaser():
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
        ys = [N["length_scaling"][f"{L}|mean"][arm] for L in Ls]
        ax.plot(xs, ys, color=C[arm], ls=LS[arm], marker=MK[arm], label=LAB[arm], mfc=("white" if arm == "A" else C[arm]))
    ax.set_xscale("log", base=2); ax.set_xticks(xs); ax.set_xticklabels(["32K", "64K", "128K"])
    ax.set_ylim(0, 0.8); ax.set_xlabel("context length (characters)"); ax.set_ylabel("needle recall (6 VLMs)")
    ax.legend(loc="center left", frameon=False, bbox_to_anchor=(0.02, 0.42), handlelength=1.8)
    ax.set_title("Equal vision-token budget", fontsize=7.5, pad=3)
    fig.savefig(FIG / "teaser.pdf"); plt.close(fig)
    return ans_a, ans_s, gold

# ---------------------------------------------------------------- length scaling
def scaling():
    Ls = ["32k", "64k", "128k"]; xs = [32, 64, 128]; ls = N["length_scaling"]
    readers = [k for k in N["reader_names"]]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.3, 1.55), gridspec_kw=dict(wspace=0.45, left=0.13, right=0.98, bottom=0.25, top=0.8))
    for ax in (a1, a2): style(ax)
    for arm in "AS":
        for rd in readers:
            a1.plot(xs, [ls[f"{L}|{rd}"][arm] for L in Ls], color=C[arm], lw=0.6, alpha=0.35, ls=LS[arm])
        a1.plot(xs, [ls[f"{L}|mean"][arm] for L in Ls], color=C[arm], marker=MK[arm], ls=LS[arm], label=LAB[arm],
                mfc=("white" if arm == "A" else C[arm]))
    a1.set_ylim(0, 1.0); a1.set_ylabel("needle recall"); a1.text(0.02, 0.97, "(a)", transform=a1.transAxes, va="top", fontsize=7.5)
    for arm in "AST":
        a2.plot(xs, [ls[f"{L}|mean"][f"billed_{arm}"] / 1000 for L in Ls], color=C[arm], marker=MK[arm], ls=LS[arm],
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
        axs[0].plot(ks, [d[str(k)][arm] for k in ks], color=C[arm], marker=MK[arm], ls=LS[arm], label=LAB[arm],
                    mfc=("white" if arm == "A" else C[arm]))
        axs[1].plot(ks, [d[str(k)][f"billed_{arm}"] / 1000 for k in ks], color=C[arm], marker=MK[arm], ls=LS[arm],
                    mfc=("white" if arm == "A" else C[arm]))
    for ax in axs[:2]:
        ax.set_xscale("log", base=2); ax.set_xticks(ks); ax.set_xticklabels([str(k) for k in ks]); ax.set_xlabel("hazardous strings per 32K-char document (k)")
    axs[0].set_ylabel("needle recall"); axs[0].set_ylim(0, 1.05); axs[0].set_title("(a) recall vs. hazard density", fontsize=7.5, pad=2)
    axs[1].set_ylabel("billed prompt tokens (K)"); axs[1].set_title("(b) cost vs. hazard density", fontsize=7.5, pad=2)
    h, l = axs[0].get_legend_handles_labels(); axs[1].legend(h, l, frameon=False, loc="upper left", fontsize=6)
    fx = [f["X"] for f in R["frontier"]]; fk = [f["K"] for f in R["frontier"]]
    axs[2].plot([p[1] for p in fk], [p[0] for p in fk], color=C["K"], marker=MK["K"], ls="-", label="route anchors-on-uniform / text")
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
    ax.axhline(0, color=MUTED, lw=0.6); ax.set_xlabel("characters per vision token (density)"); ax.set_ylabel("$\\Delta$ exact-match (ours $-$ uniform)")
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

if __name__ == "__main__":
    print("teaser answers (A, S, gold):", teaser()); scaling(); density(); phase(); print("thumbs", thumbs()); print("ok")
