# Source-document-only LaTeX manuscript

Technical content is drawn only from the Word document supplied in this user request. The two example papers provide layout and organization only. No earlier alternate trajectory data or optimization result is used.

Compile main.tex with XeLaTeX:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

For Overleaf, upload this source ZIP, choose XeLaTeX, and select main.tex. Latin Modern and standard TeX Live packages are used. The short Chinese AI prompt uses Noto Serif CJK SC or FandolSong-Regular. config.tex contains the team-number placeholder.

- main.tex: complete manuscript and the 10 source bibliography entries.
- source_plots.tex: English LaTeX label overlays for the unchanged source curves.
- tables/: all 18 substantive source tables in English typesetting.
- figures/: six original curve PNGs and three table-derived vector PDFs.

The source curves are not digitized, resimulated, or replaced. Original PNG files are unchanged. Their label regions are translated at the LaTeX typesetting layer. Additional charts use only numbers and pass/fail entries printed in the source.

The retained model-specific results are baseline 104/120 t, parameterized Powell/grid 96/110 t, and combined area/response/staging 102/110--112 t. These are source-reported results, not a new solver execution or independent physical validation.
