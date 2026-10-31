"""Reddit collage (r/dataisbeautiful style): world map of every island coloured by size, island counts by region labelled
in open ocean, the size distribution, and rankings of the most populous and largest islands. Numbers from data/results.json.
Output: reddit/world_islands.png (3000 px wide)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from figstyle import *

R = jload(f"{DATA}/results.json")
fmt = lambda v: f"{rnd(v):,}"
OUT = os.path.join(ROOT, "reddit", "world_islands.png")
HALO = [pe.withStroke(linewidth=4.5, foreground="white")]

W_IN = 15
mh = W_IN * (WEXT[3] - WEXT[2]) / (WEXT[1] - WEXT[0])
H_IN = 1.75 + mh + 3.5 + .85 + .45
fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG)
fy = lambda inch: 1 - inch / H_IN                  # inches from the top to figure fraction

# ---------- title ----------
fig.text(.022, fy(.5), "Where the world's islands are", fontproperties=DISP, fontsize=34, color=FG, va="center")
fig.text(.023, fy(1.12), f"{fmt(R['counts']['n'])} islands in the full-resolution GSHHG shoreline, {fmt(R['counts']['ge1'])} of them 1 km² or more.\n"
         f"{R['pop']['isl'] / 1e6:,.0f} million people, {R['pop']['pct']:.1f}% of humanity, live on one. Colours show island size.", family=MONO, fontsize=13, color=FG, va="center", linespacing=1.5)

# ---------- map ----------
ax = fig.add_axes([0, fy(1.75 + mh), 1, mh / H_IN]); ax.set_facecolor(BG)
ras = island_raster(width=6000, key="world")
draw_land(ax, fc="#E9E5DC", ec="#E9E5DC"); show_raster(ax, ras, WEXT); frame(ax, WEXT)
rg = {d["k"]: d for d in R["regions"]}
LAB = {"nam": (-150, 40), "car": (-42, 24.5), "sam": (-100, -46), "eur": (-30, 52), "afr": (-20, -24), "asia": (168, 33),
       "oce": (-152, -35), "ant": (100, -45)}
for k, (lo, la) in LAB.items():
    d = rg[k]; x, y = to_xy(lo, la)
    ax.text(x, y, d["name"].replace("Antarctica and the far south", "Antarctica and\nthe far south").replace("Caribbean and Central America", "Caribbean and\nCentral America"), fontproperties=DISPB, fontsize=12, color=FG, ha="center", va="bottom", path_effects=HALO, zorder=10, linespacing=1.0)
    pop = d["pop"] / 1e6
    ptxt = "nobody lives there" if pop < .05 else f"{pop:,.1f} m people" if pop < 10 else f"{pop:,.0f} m people"
    ax.text(x, y - 1.2e5, f"{fmt(d['n'])} islands\n{fmt(d['ge1'])} of 1 km² or more\n{ptxt}", family=MONO, fontsize=9, color=FG, ha="center", va="top",
            linespacing=1.35, path_effects=HALO, zorder=10)
# Java callout, in the Indian Ocean south of Java
x, y = to_xy(86, -12)
j = R["pop"]["top"][0]
ax.text(x, y, f"Java: {j['pop'] / 1e6:,.0f} m people,\nthe most of any island", family=MONO, fontsize=10, color=HOT, ha="center", va="top",
        path_effects=HALO, zorder=10, fontweight="medium")

# ---------- bottom panels ----------
top = 1.75 + mh + .35
ph = 3.5
K = R["classes"]
a1 = fig.add_axes([.035, fy(top + ph - .55), .25, (ph - 1.0) / H_IN]); clean(a1)
a1.bar(range(8), [d["n"] for d in K], color=CLASS_COL, width=.8)
for i, d in enumerate(K):
    a1.text(i, d["n"] + 1500, fmt(d["n"]), ha="center", va="bottom", fontsize=8.6, color=FG, rotation=90)
a1.set_xticks(range(8)); a1.set_xticklabels(["<0.1", "0.1-1", "1-10", "10-100", "100-1k", "1k-10k", "10k-100k", "100k+"], rotation=40, ha="right", fontsize=9)
a1.set_yticks([]); a1.spines["left"].set_visible(False); a1.set_ylim(0, K[0]["n"] * 1.35)
a1.set_title("Islands by size, km²", fontproperties=DISPB, fontsize=14, color=FG, loc="left", pad=8)
a1.text(1.6, K[0]["n"] * 1.1, f"{R['counts']['under01_pct']:.0f}% are under 0.1 km²", fontsize=9.5, color=MUT)


def rank(axx, rows, val, lab, title):
    clean(axx)
    v = [val(d) for d in rows]
    axx.barh(range(len(rows)), v, color=[CLASS_COL[size_class(d["area"])] for d in rows], height=.68)
    for i, d in enumerate(rows):
        axx.text(v[i] + max(v) * .02, i, lab(d), va="center", fontsize=9, color=FG)
    axx.set_yticks(range(len(rows))); axx.set_yticklabels([f"{d['name']}" for d in rows], fontsize=9.5)
    axx.invert_yaxis(); axx.set_xticks([]); axx.spines["bottom"].set_visible(False); axx.set_xlim(0, max(v) * 1.42)
    axx.set_title(title, fontproperties=DISPB, fontsize=14, color=FG, loc="left", pad=8)


a2 = fig.add_axes([.41, fy(top + ph - .55), .2, (ph - 1.0) / H_IN])
rank(a2, R["pop"]["top"][:10], lambda d: d["pop"] / 1e6, lambda d: f"{d['pop'] / 1e6:,.0f} m", "Most people")
a3 = fig.add_axes([.73, fy(top + ph - .55), .2, (ph - 1.0) / H_IN])
rank(a3, R["largest"][:10], lambda d: d["area"] / 1e3, lambda d: f"{fmt(d['area'])} km²", "Largest")

# legend: full class names, in its own strip
lax = fig.add_axes([.02, fy(top + ph + .38), .96, .32 / H_IN]); lax.axis("off")
hs = [Patch(fc=CLASS_COL[k], ec="none", label=CLASSES[k][1]) for k in range(8)]
lg = lax.legend(handles=hs, loc="center", ncol=8, frameon=False, fontsize=9.6, handlelength=1.2, handleheight=1.1, columnspacing=1.3,
                title=None)
fig.text(.022, fy(H_IN - .25), "Source: GSHHG 2.3 full-resolution shorelines (Wessel and Smith); WorldPop Global 2, 2025 estimate (CC BY 4.0); Natural Earth.\n"
         "Islands: all land except the five continents, plus islands in lakes and around Antarctica. Counts under 1 km² depend on the map's resolution.", family=MONO, fontsize=8.6, color=MUT, va="center", linespacing=1.4)
fig.text(.978, fy(H_IN - .25), "maps.tristanhotham.com/world-islands", family=MONO, fontsize=10, color=FG, va="center", ha="right", fontweight="medium")
fig.savefig(OUT, dpi=200, facecolor=BG)
plt.close(fig)
from PIL import Image
print(Image.open(OUT).size, os.path.getsize(OUT) // 1024, "KB")
