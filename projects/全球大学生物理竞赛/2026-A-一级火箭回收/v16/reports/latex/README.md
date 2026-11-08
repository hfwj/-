# LaTeX source: Problem A research draft

Main file: **main.tex**. Compile with **XeLaTeX** and BibTeX:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

For Overleaf, upload the source ZIP, choose XeLaTeX, and select main.tex. The package was compiled locally in an independent clean directory; it was not tested inside the Overleaf website.

A4, 11pt article; Latin Modern Roman. Standard TeX Live packages are needed. The exact Chinese AI prompt uses Noto Serif CJK SC, with FandolSong-Regular as fallback. The eight figures are vector PDFs; Python is not required to compile.

- config.tex: replace TBA with the assigned team number.
- numbers.tex and tables/: generated numerical macros and table rows.
- references.bib: bibliography, managed by BibTeX.
- figures/: vector PDFs in the portable ZIP.
- .latexmkrc: engine settings.

The repository can also locate figures at ../../results/figures; the portable ZIP uses local figures/ and has no repository or network dependency.

This is a conditional numerical research draft. The 140 t candidate is not a global minimum or robust load. Model assumptions and failed fixed-control perturbations remain explicit. Team number and complete AI transcript are unfinished. Preparing this manuscript did not rerun trajectory optimization.
