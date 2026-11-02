"""E1 text-only baseline: the same items and questions, but the raw text is given instead of the rendered image.
Writes <run>/predtext_or_<tag>.json or <run>/predtext_minimax.json keyed "T_<item>.png" (scored as arm T).
usage: MODEL=openai/gpt-6-luna python3 run_text.py run3_s6 ruler_s6_single_3 ...
       MODEL=minimax python3 run_text.py ...        (MiniMax-M3 via mmx)"""
import json, os, subprocess, sys, tempfile, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from run_minimax import PROMPT, parse

HERE = Path(__file__).parent
MODEL = os.environ["MODEL"]; MINIMAX = MODEL == "minimax"
RAW = bool(os.environ.get("RAW"))  # LongBench: keep the free-form answer instead of parsing JSON
IMG_INTRO = "This image is a block of rendered English text with identifiers embedded."

def prompts(run):
    gt = json.loads((HERE / run / "gt.json").read_text())
    if isinstance(gt, dict) and "items" in gt:  # RULER / LongBench: per-item template with an image placeholder
        return {it["item"]: it["prompt"].replace(it.get("placeholder", "[The text is rendered in the image above.]"), it["text"])
                for it in gt["items"]}
    return {it["item"]: "Text:\n" + it["text"] + "\n\n" + PROMPT.replace(IMG_INTRO, "The text above is a block of English text with identifiers embedded.")
            for it in gt}

def call(prompt):
    if MINIMAX:
        msgs = [{"role": "user", "content": prompt}]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f: json.dump(msgs, f)
        r = subprocess.run(["mmx", "text", "chat", "--model", "MiniMax-M3", "--messages-file", f.name, "--temperature", "0.01",
                            "--output", "json", "--non-interactive", "--quiet"], capture_output=True, text=True, timeout=300)
        try: txt = json.loads(r.stdout).get("content", r.stdout)
        except json.JSONDecodeError: txt = r.stdout
        return (txt if isinstance(txt, str) else json.dumps(txt)), {}
    from run_openrouter import KEY, CTX
    body = {"model": MODEL, "temperature": 0, "max_tokens": int(os.environ.get("MAXTOK", 2000)),
            **({"reasoning": {"effort": os.environ["EFFORT"]}} if os.environ.get("EFFORT") else {}),
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300, context=CTX) as r: j = json.loads(r.read())
    return j["choices"][0]["message"].get("content") or "", j.get("usage", {})

def read(arg, tries=4):
    item, prompt = arg; err = ""
    for k in range(tries):
        try:
            txt, usage = call(prompt)
            p = {"text": txt.strip()} if RAW else parse(txt)
            if p is not None and (not RAW or txt.strip()): return f"T_{item}.png", p | {"usage": usage}
            err = txt[-300:]
        except Exception as e:
            err = repr(e)[-300:]; time.sleep(2 * (k + 1))
    return f"T_{item}.png", {"ids": [], "codename": "", "error": err}

if __name__ == "__main__":
    tag = "minimax" if MINIMAX else "or_" + MODEL.split("/")[-1]
    for run in sys.argv[1:]:
        f, todo = HERE / run / f"predtext_{tag}.json", prompts(run)
        old = json.loads(f.read_text()) if os.environ.get("RETRY") and f.exists() else {}
        todo = {i: q for i, q in todo.items() if "error" in old.get(f"T_{i}.png", {"error": 1})}  # RETRY: failed items only
        with ThreadPoolExecutor(4 if MINIMAX else 8) as ex: out = old | dict(ex.map(read, todo.items()))
        f.write_text(json.dumps(out, indent=1))
        print(run, MODEL, len(out), "items,", sum("error" in v for v in out.values()), "errors, cost $%.3f" %
              sum(v.get("usage", {}).get("cost", 0) or 0 for v in out.values()))
