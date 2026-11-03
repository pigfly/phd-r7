"""Fingerprint numbers, citation keys, and labels/refs in the prose files, to verify an editing pass changed none.
usage: python3 data/humanizer_guard.py snapshot | check"""
import json, re, sys
from collections import Counter
from pathlib import Path
FILES = [f"sec/{f}" for f in ("0_abstract.tex", "1_intro.tex", "2_related.tex", "3_method.tex", "4_setup.tex", "5_results.tex",
                              "6_conclusion.tex", "7_llm_statement.tex", "X_appendix.tex")] + ["fig/method.tex"]
SNAP = Path("data/.humanizer_snapshot.json")
def fp(t):
    t = re.sub(r"(?<!\\)%.*", "", t)
    nums = re.findall(r"(?<![A-Za-z\\])[-+]?\d+(?:[.,]\d+)*", t)
    cites = [k.strip() for m in re.findall(r"\\cite[pt]?\{([^}]*)\}", t) for k in m.split(",")]
    refs = re.findall(r"\\(?:c?ref|Cref|label|input|includegraphics(?:\[[^]]*\])?)\{([^}]*)\}", t)
    return dict(nums=Counter(nums), cites=Counter(cites), refs=Counter(refs))
if sys.argv[1] == "snapshot":
    SNAP.write_text(json.dumps({f: {k: dict(v) for k, v in fp(Path(f).read_text()).items()} for f in FILES}))
    print("snapshot of", len(FILES), "files")
else:
    old = json.loads(SNAP.read_text()); bad = 0
    for f in FILES:
        new = fp(Path(f).read_text())
        for k in ("nums", "cites", "refs"):
            o, n = Counter(old[f][k]), new[k]
            if o != n:
                bad += 1; print(f"{f} {k}: removed {dict(o - n)} added {dict(n - o)}")
    print("OK: no number, citation, or label changed" if not bad else f"{bad} differences")
