"""Where do real long texts fall on the routing feature r = anchor tokens / S-image vision tokens?
32K-char chunks from LongBench (English tasks), PG essays, Python source (site-packages), local system logs and
package RECORD manifests; S rendered for every chunk (6px). Text tokens estimated with a 2-feature linear fit
(plain chars, flagged chars) calibrated on billed text-only reads of the density sweep (GPT-6-luna).
Policy cost: r <= TAU -> S vision tokens + anchors, else plain text.
usage: python3 real_density.py  -> prints table, writes analysis_real_density.json"""
import glob, json, os, random, re, site, statistics as St
from multiprocessing import Pool
from pathlib import Path
import make_items as M

HERE = Path(__file__).parent; CH = 32000; PER = 40; TAU = 0.3; R = random.Random(0)

def chunks(text, n=PER):
    text = re.sub(r"\s+", " ", "".join(c if c.isascii() else "?" for c in text))
    idx = list(range(0, max(1, len(text) - CH), CH)); R.shuffle(idx)
    return [text[i:i + CH] for i in idx[:n] if len(text[i:i + CH]) > CH * 0.9]

def corpora():
    c = {}
    lb = HERE / "longbench" / "data"
    for t in ["narrativeqa", "qasper", "multifieldqa_en", "hotpotqa", "2wikimqa", "musique", "gov_report", "qmsum",
              "multi_news", "triviaqa", "passage_retrieval_en", "lcc", "repobench-p"]:
        rows = [json.loads(l) for l in open(lb / f"{t}.jsonl")]; R.shuffle(rows)
        c[f"longbench/{t}"] = chunks(" ".join(r["context"] for r in rows[:200]), 20)
    c["pg_essays"] = chunks(json.loads((HERE / "ruler" / "pg_essays.json").read_text())["text"])
    py = sorted(glob.glob(os.path.join(site.getsitepackages()[0], "**", "*.py"), recursive=True)); R.shuffle(py)
    c["python_source"] = chunks(" ".join(open(f, errors="ignore").read() for f in py[:400]))
    logs = ""
    for f in ["/var/log/install.log", "/var/log/fsck_apfs.log", "/var/log/wifi.log"]:
        try: logs += open(f, errors="ignore").read()[-3_000_000:] + " "
        except OSError: pass
    c["system_logs"] = chunks(logs)
    rec = " ".join(open(f, errors="ignore").read() for f in glob.glob(os.path.join(site.getsitepackages()[0], "*.dist-info", "RECORD")))
    c["pkg_manifests"] = chunks(rec)
    return c

def measure(text):
    M.STRICT = True
    fl = [w.strip(".,;:()[]\"'") for w in M.words(text) if M.flagged(w)]
    M.STRICT = False
    anchor = round(sum(len(t) / 2 + 3 for t in fl))
    bud = M.vtokens(*M.render(M.units_uniform(text, 6)).size)
    s_im = M.long_arm("S", text, bud, 6)[0]
    return dict(chars=len(text), n_flag=len(fl), flag_chars=sum(len(t) for t in fl), anchor=anchor, a_vtok=bud, s_vtok=M.vtokens(*s_im.size))

def calibrate():
    """billed text tokens ~ a * plain_chars + b * flagged_chars (least squares, GPT text reads on rdens)"""
    xs, ys = [], []
    for run in sorted(HERE.glob("rdens_k*")):
        items = {it["item"]: it for it in json.loads((run / "gt.json").read_text())["items"]}
        for k, p in json.loads((run / "predtext_or_gpt-6-luna.json").read_text()).items():
            b = p.get("usage", {}).get("prompt_tokens")
            if not b: continue
            t = items[int(k[2:-4])]["text"]; M.STRICT = True
            fc = sum(len(w.strip(".,;:()[]\"'")) for w in M.words(t) if M.flagged(w)); M.STRICT = False
            xs.append((len(t) - fc, fc)); ys.append(b)
    s11 = sum(x[0] ** 2 for x in xs); s22 = sum(x[1] ** 2 for x in xs); s12 = sum(x[0] * x[1] for x in xs)
    s1y = sum(x[0] * y for x, y in zip(xs, ys)); s2y = sum(x[1] * y for x, y in zip(xs, ys)); det = s11 * s22 - s12 ** 2
    a, b = (s1y * s22 - s2y * s12) / det, (s2y * s11 - s1y * s12) / det
    err = St.mean(abs(a * x[0] + b * x[1] - y) / y for x, y in zip(xs, ys))
    return a, b, err

if __name__ == "__main__":
    a, b, err = calibrate()
    print(f"text-token fit: {a:.4f}/plain char + {b:.4f}/flagged char  (mean abs rel err {err:.1%}; = {1/a:.2f} plain chars/token)")
    cor = corpora(); jobs = [(name, t) for name, ts in cor.items() for t in ts]
    with Pool(16) as pool: ms = pool.map(measure, [t for _, t in jobs])
    res = {}
    print(f"\n{'corpus':32s} {'n':>3s} {'flag/1K':>8s} {'r med':>6s} {'r p90':>6s} {'->X':>5s} {'cost/T':>7s}")
    for name in cor:
        rows = [m for (n, _), m in zip(jobs, ms) if n == name]
        if not rows: continue
        for m in rows:
            m["r"] = m["anchor"] / m["s_vtok"]; m["text_tok"] = a * (m["chars"] - m["flag_chars"]) + b * m["flag_chars"]
            m["route_X"] = m["r"] <= TAU; m["cost"] = (m["s_vtok"] + m["anchor"]) if m["route_X"] else m["text_tok"]
        rs = sorted(m["r"] for m in rows)
        res[name] = dict(n=len(rows), flag_per_1k=St.mean(1000 * m["n_flag"] / m["chars"] for m in rows), r_median=St.median(rs),
                         r_p90=rs[int(0.9 * (len(rs) - 1))], frac_X=St.mean(m["route_X"] for m in rows),
                         cost_rel=sum(m["cost"] for m in rows) / sum(m["text_tok"] for m in rows))
        v = res[name]
        print(f"{name:32s} {v['n']:3d} {v['flag_per_1k']:8.2f} {v['r_median']:6.2f} {v['r_p90']:6.2f} {v['frac_X']:5.0%} {v['cost_rel']:7.2f}")
    (HERE / "analysis_real_density.json").write_text(json.dumps(dict(fit=[a, b, err], tau=TAU, corpora=res), indent=1))
