"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/Hotham_World_Islands.pdf and .tex (figures f_*.png sit beside them)."""
import re, subprocess, importlib.util
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "07_build_site.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))          # runs the shared fact checks
R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_World_Islands"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
KEEP = {"DOI"}

# facts stated in words only in the paper
assert len(R["shared"]) == 8 and R["shared"][0]["name"] == "New Guinea" and R["shared"][0]["shares"][0][0] == "PNG"
assert [R["regions"][i]["k"] for i in (0, 1, 2)] == ["eur", "asia", "afr"]
assert R["largest_lake"][0]["name"] == "Manitoulin Island" and R["largest_lake"][1]["name"] == "René-Levasseur Island"
assert R["largest_ant"][0]["name"] == "Adelaide"
lk = {d["name"]: d["pop"] for d in R["largest_lake"]}
assert lk["Montreal and Laval (joined in GSHHG)"] + lk["Mekong and Bassac river island (as drawn in GSHHG)"] > R["pop"]["lake_pop"] / 2
assert R["island_nations"]["mixed"][1]["c"] == "GNQ" and R["top_sov"][1]["sov"] == "DN1"
assert R["counts"]["ge1000"] == 296


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{rnd(v):,}"
    if f == "pc": return f"{rnd(v)}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "m0": return f"{rnd(v / 1e6):,}"
    if f == "m1": return f"{v / 1e6:,.1f}"
    return tex(str(v))


C = R["counts"]
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Sources, what was used and licences.}\\label{tab:sources}"
      "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{3.2cm}>{\\raggedright\\arraybackslash}p{7.6cm}>{\\raggedright\\arraybackslash}p{2.6cm}}\\toprule Source & Used & Licence\\\\\\midrule\n"
      f"GSHHG 2.3, full & {C['n']:,} islands ({C['sea']:,} sea, {C['lake']:,} lake, {C['ant']} Antarctic); {C['lakes']:,} lakes & LGPL-3.0\\\\\n"
      "GSHHG 2.3, other resolutions & Island counts (crude, low, intermediate, high) & LGPL-3.0\\\\\n"
      f"WorldPop Global 2, 2025 & {R['meta']['n_cells']:,} populated cells at 30 arc seconds & CC BY 4.0\\\\\n"
      "Natural Earth 10m & Countries, island names, land and minor islands, places & Public domain\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(d['label'])} & {d['n']:,} & {d['ge01']:,} & {d['ge1']:,} & {d['ge10']:,} & {d['ge100']:,} & {d['ge1000']:,}\\\\\n" for d in R["res"])
TRS = ("\\begin{table}[tbp]\\centering\\small\\caption{Islands by map and resolution, all sizes and at or above each area (km$^2$).}\\label{tab:res}"
       "\\begin{tabular}{lrrrrrr}\\toprule Map & All & 0.1+ & 1+ & 10+ & 100+ & 1,000+\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(d['name'])} & {d['n']:,} & {d['ge1']:,} & {d['ge10']:,} & {d['ge100']:,} & {rnd(d['area']):,}\\\\\n" for d in R["top_countries"]["ge1"][:15])
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Islands by country or territory (top 15 by islands of 1 km$^2$ or more), with island land area.}\\label{tab:cty}"
      "\\begin{tabular}{lrrrrr}\\toprule Country or territory & All & 1+ km$^2$ & 10+ km$^2$ & 100+ km$^2$ & Area, km$^2$\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{d['rank_pop']} & {tex(d['name'])} & {tex(d['cname'])} & {rnd(d['area']):,} & {d['pop'] / 1e6:.2f} & {rnd(d['dens']):,}\\\\\n" for d in R["pop"]["top"][:25])
TP = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The 25 most populous islands, WorldPop 2025.}\\label{tab:pop}"
      "\\begin{tabular}{rllrrr}\\toprule & Island & Country & Area, km$^2$ & People, m & Per km$^2$\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(m.group(1)), m.group(3) or "raw"), t)
t = t.replace("{{TABLE_SOURCES}}", TS).replace("{{TABLE_RES}}", TRS).replace("{{TABLE_CTY}}", TC).replace("{{TABLE_POP}}", TP)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP
assert "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
