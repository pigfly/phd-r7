#!/bin/zsh
# Build the paper and split it into main.pdf (paper + references + LLM statement) and supplementary.pdf.
cd "${0:A:h}"
pdflatex -interaction=nonstopmode -jobname=full main >/dev/null; bibtex full >/dev/null
pdflatex -interaction=nonstopmode -jobname=full main >/dev/null; pdflatex -interaction=nonstopmode -jobname=full main >/dev/null
grep -E "^!|undefined" full.log && exit 1
n=$(pdfinfo full.pdf | awk '/^Pages/ {print $2}')
s=$(python3 -c "
import subprocess
for p in range(1, $n + 1):
    t = subprocess.run(['pdftotext', '-f', str(p), '-l', str(p), 'full.pdf', '-'], capture_output=True, text=True).stdout
    if 'Supplementary Material' in t: print(p); break")
python3 - "$s" <<'PY'
import sys
from pypdf import PdfReader, PdfWriter
s = int(sys.argv[1]); r = PdfReader("full.pdf")
for name, pages in (("main.pdf", range(0, s - 1)), ("supplementary.pdf", range(s - 1, len(r.pages)))):
    w = PdfWriter()
    for i in pages: w.add_page(r.pages[i])
    w.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
    with open(name, "wb") as f: w.write(f)
PY
echo "main.pdf: pages 1-$((s-1)); supplementary.pdf: pages $s-$n of full.pdf"
