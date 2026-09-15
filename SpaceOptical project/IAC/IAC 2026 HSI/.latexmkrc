# iac.cls loads fontspec (TeX Gyre Termes), which needs LuaTeX or XeTeX.
# pdfLaTeX aborts with "Fatal Package fontspec Error", so build with LuaLaTeX.
$pdf_mode = 4;          # 4 = lualatex
$bibtex_use = 2;        # run biber and clean its output
