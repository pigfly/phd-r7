"""Merge the R/X arms (rabl_*) into the Table-1 runs (rbase_*) item-by-item -> rbx_* (same items, same seeds).
usage: python3 merge_rbx.py"""
import json, shutil
from pathlib import Path
HERE = Path(__file__).parent
for b in sorted(HERE.glob("rbase_s*")):
    x = HERE / b.name.replace("rbase", "rabl"); out = HERE / b.name.replace("rbase", "rbx"); out.mkdir(exist_ok=True)
    gb, gx = json.loads((b / "gt.json").read_text()), json.loads((x / "gt.json").read_text())
    assert all(p["text"] == q["text"] for p, q in zip(gb["items"], gx["items"])), b.name
    man = json.loads((b / "manifest.json").read_text()) + [m | {"name": "B_" + m["name"]} for m in json.loads((x / "manifest.json").read_text())]
    (out / "manifest.json").write_text(json.dumps(man, indent=1)); shutil.copy(b / "gt.json", out / "gt.json")
    for f in b.glob("pred_*.json"):
        pred = json.loads(f.read_text())
        if (x / f.name).exists(): pred |= {"B_" + k: v for k, v in json.loads((x / f.name).read_text()).items()}
        (out / f.name).write_text(json.dumps(pred, indent=1))
    print(out.name, len(man), "manifest rows")
