"""Second reader: MiniMax-M3 via `mmx text chat` (Anthropic-style image block), one stateless call per image.
usage: python3 run_minimax.py run_s5 run_s6      -> writes <run>/pred_minimax.json, then: python3 score.py <run> <run>/pred_minimax.json"""
import base64, json, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MODEL = "MiniMax-M3"
PROMPT_V1 = ('This image is a block of rendered English text with identifiers embedded. Extract (1) every identifier-like '
          'string exactly as written, character for character: hex strings, UUIDs, file paths, IP:port addresses, numbers '
          'with 4+ digits; if unsure of a character give your best reading anyway; (2) the word in the sentence '
          '"The release codename is ___." Return ONLY JSON: {"ids": [...], "codename": "..."}')

PROMPT_V3 = ('This image is a block of rendered English text with identifiers embedded. Extract (1) every identifier-like '
             'string exactly as written, character for character (case-sensitive): hashes (hex or base64), UUIDs, file paths, '
             'IP:port addresses, numbers with 4+ digits; if unsure of a character give your best reading anyway; (2) the words '
             'completing: "The release codename is ___.", "The team mascot is a ___.", "The backup server is named ___." '
             'Return ONLY JSON: {"ids": [...], "codename": "...", "mascot": "...", "server": "..."}')
UNREADABLE = (' If you cannot read every character of an identifier with confidence, output the literal string "[unreadable]" '
              'in its place instead of guessing.')
import os
PROMPT = PROMPT_V3 if os.environ.get("PROMPT", "v3") == "v3" else PROMPT_V1
if os.environ.get("UNREADABLE"): PROMPT = PROMPT.replace(" if unsure of a character give your best reading anyway;", "") + UNREADABLE
OUTNAME = os.environ.get("OUTNAME", "pred_minimax.json")
ARMS = os.environ.get("ARMS")  # optional: only images of these arms

def parse(txt):
    j, dec = None, json.JSONDecoder()
    for m in re.finditer(r"\{", txt):  # first decodable JSON object (readers sometimes add prose after the JSON)
        try:
            j = dec.raw_decode(txt[m.start():])[0]; break
        except json.JSONDecodeError:
            continue
    if not isinstance(j, dict): return None
    if "content" in j and isinstance(j["content"], str):  # wrapped response
        return parse(j["content"])
    return {"ids": [str(x) for x in j.get("ids", [])], **{k: str(j.get(k, "")) for k in ("codename", "mascot", "server")}}

def raw(txt):
    """free-form answer (LongBench): unwrap the mmx JSON envelope if present"""
    try: j = json.loads(txt); txt = j.get("content", txt) if isinstance(j, dict) else txt
    except json.JSONDecodeError: pass
    return {"text": txt.strip()} if isinstance(txt, str) and txt.strip() else None

def sidecar(img: Path):
    t = img.with_suffix(".txt")
    return ("\n\n" + t.read_text()) if t.exists() else ""

def prompt_for(img: Path):
    """per-image prompt file (RULER runs) overrides the default extraction prompt"""
    q = img.with_suffix(".prompt")
    return q.read_text() if q.exists() else PROMPT + sidecar(img)

def read(img: Path, tries=3):
    b = base64.b64encode(img.read_bytes()).decode()
    msgs = [{"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b}},
                                         {"type": "text", "text": prompt_for(img)}]}]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f: json.dump(msgs, f)
    for _ in range(tries):
        r = subprocess.run(["mmx", "text", "chat", "--model", MODEL, "--messages-file", f.name, "--temperature", "0.01",
                            "--output", "json", "--non-interactive", "--quiet"], capture_output=True, text=True, timeout=300)
        p = raw(r.stdout) if img.with_suffix(".raw").exists() else parse(r.stdout)
        if p is not None: return img.name, p
    return img.name, {"ids": [], "codename": "", "error": (r.stdout + r.stderr)[-300:]}

def main():
  for run in sys.argv[1:]:
    imgs = sorted((Path(__file__).parent / run / "img").glob("*.png"))
    if ARMS:
        man = {m["name"]: m["arm"] for m in json.loads((Path(__file__).parent / run / "manifest.json").read_text())}
        imgs = [p for p in imgs if man[p.stem] in ARMS]
    f = Path(__file__).parent / run / OUTNAME
    old = json.loads(f.read_text()) if os.environ.get("RETRY") and f.exists() else {}
    if old: imgs = [i for i in imgs if "error" in old.get(i.name, {"error": 1})]  # RETRY: failed images only
    with ThreadPoolExecutor(4) as ex: out = old | dict(ex.map(read, imgs))
    f.write_text(json.dumps(out, indent=1))
    print(run, len(out), "images,", sum("error" in v for v in out.values()), "errors")

if __name__ == "__main__":
    main()
