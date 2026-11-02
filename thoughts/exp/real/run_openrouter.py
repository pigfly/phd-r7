"""More readers via OpenRouter (OpenAI-compatible chat API), one stateless call per image; same prompt as run_minimax.py.
Records the provider-billed usage (prompt/completion tokens) per image.
usage: MODEL=openai/gpt-6-luna python3 run_openrouter.py run3_s5 run3_s6 ...   -> <run>/pred_or_<tag>.json
       LIMIT=1 for a smoke test (first image only, nothing written)."""
import base64, json, os, ssl, sys, time, urllib.request
import certifi
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from run_minimax import parse, prompt_for

HERE = Path(__file__).parent
KEY = next(l.split("=", 1)[1].strip().strip('"') for l in (HERE.parents[2] / ".env").read_text().splitlines()
           if l.startswith("OPENROUTER_API_KEY="))
MODEL = os.environ["MODEL"]; TAG = MODEL.split("/")[-1]
CTX = ssl.create_default_context(cafile=certifi.where())
LIMIT = int(os.environ.get("LIMIT", 0)); WORKERS = int(os.environ.get("WORKERS", 8))

def call(img: Path):
    b = base64.b64encode(img.read_bytes()).decode()
    body = {"model": MODEL, "temperature": 0, "max_tokens": int(os.environ.get("MAXTOK", 2000)),
            **({"reasoning": {"effort": os.environ["EFFORT"]}} if os.environ.get("EFFORT") else {}),
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b}"}},
                {"type": "text", "text": prompt_for(img)}]}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300, context=CTX) as r: return json.loads(r.read())

def read(img: Path, tries=4):
    err = ""
    for k in range(tries):
        try:
            j = call(img); txt = j["choices"][0]["message"].get("content") or ""
            p = parse(txt)
            if p is not None: return img.name, p | {"usage": j.get("usage", {})}
            err = txt[-300:]
        except Exception as e:
            err = repr(e)[-300:]; time.sleep(2 * (k + 1))
    return img.name, {"ids": [], "codename": "", "error": err}

if __name__ == "__main__":
  for run in sys.argv[1:]:
    imgs = sorted((HERE / run / "img").glob("*.png"))
    if LIMIT:
        for i in imgs[:LIMIT]: print(MODEL, read(i))
        continue
    f = HERE / run / f"pred_or_{TAG}.json"
    if os.environ.get("RETRY") and f.exists():  # re-read only failed images, keep the rest
        old = json.loads(f.read_text()); imgs = [i for i in imgs if "error" in old.get(i.name, {"error": 1})]
    else: old = {}
    with ThreadPoolExecutor(WORKERS) as ex: out = old | dict(ex.map(read, imgs))
    f.write_text(json.dumps(out, indent=1))
    u = [v.get("usage", {}) for v in out.values()]
    print(run, MODEL, len(out), "images,", sum("error" in v for v in out.values()), "errors,",
          "cost $%.3f" % sum(x.get("cost", 0) or 0 for x in u))
