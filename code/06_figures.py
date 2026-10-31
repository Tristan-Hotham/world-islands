"""Figures for the paper (release/paper/f_*.png) and blog (release/blog/b_*.png), and the social card (header.png)."""
import shutil
import matplotlib.patheffects
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
from figstyle import *

R = jload(f"{DATA}/results.json")
PAP = os.path.join(ROOT, "release", "paper"); BLG = os.path.join(ROOT, "release", "blog")
os.makedirs(PAP, exist_ok=True); os.makedirs(BLG, exist_ok=True)
fmt = lambda v: f"{rnd(v):,}"
C = R["counts"]
POLY = jload(f"{WORK}/polys.json")
GW = pickle.load(open(f"{WORK}/polys.pkl", "rb"))
CL = [c[1] for c in CLASSES]


def both(fig, name, blog=True):
    save(fig, f"{PAP}/f_{name}.png")
    if blog:
        shutil.copy(f"{PAP}/f_{name}.png", f"{BLG}/b_{name}.png")


def class_legend(ax, loc="lower left", fs=9, anchor=None, ncol=1, title="Island size"):
    hs = [Patch(fc=CLASS_COL[k], ec="none", label=CL[k]) for k in range(len(CL))]
    lg = ax.legend(handles=hs, loc=loc, bbox_to_anchor=anchor, frameon=True, fontsize=fs, framealpha=.94, facecolor=BG, edgecolor=RULE,
                   borderpad=.8, ncol=ncol, title=title, title_fontsize=fs + .5, handlelength=1.1, handleheight=1.1)
    lg.get_title().set_color(FG)
    for t in lg.get_texts():
        t.set_color(FG)
    return lg


# ---------- 1. world map ----------
ras = island_raster()
fig = plt.figure(figsize=(14, 14 * (WEXT[3] - WEXT[2]) / (WEXT[1] - WEXT[0])), facecolor=BG)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(BG)
draw_land(ax, fc="#E9E5DC", ec="#E9E5DC"); show_raster(ax, ras, WEXT); frame(ax, WEXT)
ax.text(.012, .60, f"{fmt(C['n'])} islands", transform=ax.transAxes, fontproperties=DISPB, fontsize=24, color=FG, va="top")
ax.text(.012, .545, f"every island in the GSHHG full-resolution\nshoreline, coloured by size;\n{fmt(C['ge1'])} are 1 km² or more",
        transform=ax.transAxes, family=MONO, fontsize=10.5, color=MUT, va="top", linespacing=1.4)
class_legend(ax, anchor=(.005, .02), fs=9)
both(fig, "map_world")

# ---------- 2. three views of the size classes ----------
K = R["classes"]
fig, axs = plt.subplots(1, 3, figsize=(13, 4.8), facecolor=BG)
for ax, key, ttl, fn in ((axs[0], "n", "Islands", lambda v: fmt(v)), (axs[1], "pct_area", "Share of island area", lambda v: f"{v:.1f}%"),
                         (axs[2], "pct_pop", "Share of island people", lambda v: f"{v:.1f}%")):
    clean(ax)
    v = [d[key] for d in K]
    ax.bar(range(8), v, color=CLASS_COL, width=.78)
    for i, x in enumerate(v):
        ax.text(i, x + max(v) * .015, fn(x), ha="center", va="bottom", fontsize=7.6, color=FG, rotation=90 if key == "n" else 0)
    ax.set_xticks(range(8)); ax.set_xticklabels(["<0.1", "0.1-1", "1-10", "10-100", "100-1k", "1k-10k", "10k-100k", "100k+"], rotation=45, ha="right", fontsize=8.5)
    ax.set_title(ttl, fontproperties=DISPB, fontsize=14, color=FG, loc="left")
    ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.set_ylim(0, max(v) * 1.25)
axs[0].set_xlabel("km²", fontsize=9, color=MUT); axs[1].set_xlabel("km²", fontsize=9, color=MUT); axs[2].set_xlabel("km²", fontsize=9, color=MUT)
fig.tight_layout()
both(fig, "sizes")

# ---------- 3. the count depends on the map ----------
RS = R["res"]
fig, axs = plt.subplots(1, 2, figsize=(12, 4.6), facecolor=BG)
for ax, key, ttl in ((axs[0], "n", "All islands the map draws"), (axs[1], "ge1", "Islands of 1 km² or more")):
    clean(ax)
    v = [d[key] for d in RS]
    ax.barh(range(len(RS)), v, color=[GOLD if d["k"] == "ne" else COOL for d in RS], height=.66)
    for i, x in enumerate(v):
        ax.text(x + max(v) * .015, i, fmt(x), va="center", fontsize=9.5, color=FG)
    ax.set_yticks(range(len(RS))); ax.set_yticklabels([d["label"] for d in RS], fontsize=10)
    ax.invert_yaxis(); ax.set_xticks([]); ax.spines["bottom"].set_visible(False)
    ax.set_xlim(0, max(v) * 1.22)
    ax.set_title(ttl, fontproperties=DISPB, fontsize=14, color=FG, loc="left")
fig.tight_layout()
both(fig, "resolutions")

# ---------- 4. countries ----------
T = R["top_countries"]["ge1"][:15]
fig, ax = plt.subplots(figsize=(10, 6.2), facecolor=BG); clean(ax)
ax.barh(range(len(T)), [d["ge1"] for d in T], color=COOL, height=.66)
for i, d in enumerate(T):
    ax.text(d["ge1"] + 40, i, f"{fmt(d['ge1'])}   ({fmt(d['n'])} of all sizes)", va="center", fontsize=9.5, color=FG)
ax.set_yticks(range(len(T))); ax.set_yticklabels([d["name"] for d in T], fontsize=10.5); ax.invert_yaxis()
ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.set_xlim(0, T[0]["ge1"] * 1.5)
ax.set_title("Islands of 1 km² or more, by country or territory", fontproperties=DISPB, fontsize=15, color=FG, loc="left")
fig.tight_layout()
both(fig, "countries")

# ---------- 5. most populous islands ----------
T = R["pop"]["top"][:20]
fig, ax = plt.subplots(figsize=(10, 7.2), facecolor=BG); clean(ax)
ax.barh(range(len(T)), [d["pop"] / 1e6 for d in T], color=[CLASS_COL[size_class(d["area"])] for d in T], height=.68)
for i, d in enumerate(T):
    ax.text(d["pop"] / 1e6 + 1.5, i, f"{d['pop'] / 1e6:.1f} m", va="center", fontsize=9.5, color=FG)
ax.set_yticks(range(len(T))); ax.set_yticklabels([f"{d['name']}, {d['cname'].replace('United Kingdom', 'UK').replace('United States', 'US')}" for d in T], fontsize=10)
ax.invert_yaxis(); ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.set_xlim(0, T[0]["pop"] / 1e6 * 1.15)
ax.set_title("The most populous islands (people, 2025)", fontproperties=DISPB, fontsize=15, color=FG, loc="left")
class_legend(ax, loc="lower right", fs=8.5)
fig.tight_layout()
both(fig, "populous")

# ---------- 6. largest islands ----------
T = R["largest"][:20]
fig, ax = plt.subplots(figsize=(10, 7.2), facecolor=BG); clean(ax)
ax.barh(range(len(T)), [d["area"] / 1e3 for d in T], color=[CLASS_COL[size_class(d["area"])] for d in T], height=.68)
for i, d in enumerate(T):
    ax.text(d["area"] / 1e3 + 20, i, f"{fmt(d['area'])} km²  ·  {d['pop'] / 1e6:.1f} m people" if d["pop"] >= 5e4 else f"{fmt(d['area'])} km²  ·  {fmt(d['pop'])} people",
            va="center", fontsize=9, color=FG)
ax.set_yticks(range(len(T))); ax.set_yticklabels([d["name"] for d in T], fontsize=10)
ax.invert_yaxis(); ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.set_xlim(0, T[0]["area"] / 1e3 * 1.45)
ax.set_title("The largest islands", fontproperties=DISPB, fontsize=15, color=FG, loc="left")
fig.tight_layout()
both(fig, "largest", blog=False)

# ---------- 7. crowded and empty ----------
fig, axs = plt.subplots(1, 2, figsize=(13, 5.4), facecolor=BG)
T = R["dens"]["ge100"][:10]
ax = axs[0]; clean(ax)
ax.barh(range(len(T)), [d["dens"] for d in T], color=HOT, height=.66)
for i, d in enumerate(T):
    ax.text(d["dens"] + 250, i, f"{fmt(d['dens'])} per km²", va="center", fontsize=9, color=FG)
ax.set_yticks(range(len(T))); ax.set_yticklabels([f"{d['name'] or 'unnamed'}, {d['cname'].replace('United States', 'US')}" for d in T], fontsize=9.5)
ax.invert_yaxis(); ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.set_xlim(0, T[0]["dens"] * 1.45)
ax.set_title("Most crowded islands of 100 km² or more", fontproperties=DISPB, fontsize=13.5, color=FG, loc="left")
T = R["empty"][:10]
ax = axs[1]; clean(ax)
ax.barh(range(len(T)), [d["area"] for d in T], color="#8C8574", height=.66)
for i, d in enumerate(T):
    ax.text(d["area"] + 800, i, f"{fmt(d['area'])} km²", va="center", fontsize=9, color=FG)
ax.set_yticks(range(len(T))); ax.set_yticklabels([f"{d['name'] or 'unnamed'}, {d['cname']}" for d in T], fontsize=9.5)
ax.invert_yaxis(); ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.set_xlim(0, T[0]["area"] * 1.4)
ax.set_title("Largest islands with no one counted", fontproperties=DISPB, fontsize=13.5, color=FG, loc="left")
fig.tight_layout()
both(fig, "crowded_empty")


# ---------- regional close-ups from the full shoreline ----------
def closeup(ax, w, s, e, n, lw=0.0, title=None):
    box = shapely.box(w, s, e, n)
    sel = [i for i, p in enumerate(POLY) if p["kind"] != "antcont" and not (p["bounds"][2] < w or p["bounds"][0] > e or p["bounds"][3] < s or p["bounds"][1] > n)]
    sel.sort(key=lambda i: (POLY[i]["lvl"], -abs(POLY[i]["area"])))
    k = np.cos(np.radians((s + n) / 2))
    verts, fcs = [], []
    for i in sel:
        p = POLY[i]
        g = shapely.from_wkb(GW[i])
        if len(shapely.get_coordinates(g)) > 3000:
            g = shapely.clip_by_rect(g, w - .5, s - .5, e + .5, n + .5)
        for q in getattr(g, "geoms", [g]):
            if q.is_empty or q.geom_type != "Polygon":
                continue
            a = np.array(q.exterior.coords); a[:, 0] *= k
            verts.append(a)
            fcs.append(SEA if p["kind"] == "lake" else "#D6D0C4" if p["kind"] == "continent" else CLASS_COL[size_class(abs(p["area"]))])
    ax.add_collection(PolyCollection(verts, facecolors=fcs, edgecolors="none", linewidths=lw, zorder=2))
    ax.set_xlim(w * k, e * k); ax.set_ylim(s, n); ax.set_aspect("equal"); ax.set_facecolor(SEA)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color(RULE)
    if title:
        ax.set_title(title, fontproperties=DISPB, fontsize=12.5, color=FG, loc="left")
    return k


# Baltic archipelago: Stockholm, Aland, Turku
fig = plt.figure(figsize=(12, 6.6), facecolor=BG); ax = fig.add_axes([.01, .01, .98, .9])
k = closeup(ax, 17.6, 59.05, 23.4, 60.75)
n_box = R["baltic_n"]
fig.text(.012, .955, f"{fmt(n_box)} islands between Stockholm and Turku", fontproperties=DISPB, fontsize=17, color=FG, va="center")
for nm, lo, la in (("Stockholm", 18.07, 59.33), ("Åland", 19.95, 60.18), ("Turku", 22.27, 60.45), ("Mariehamn", 19.93, 60.10)):
    ax.plot(lo * k, la, "o", ms=4, color=FG, zorder=5)
    ax.text(lo * k + .04, la + .03, nm, fontsize=10, color=FG, zorder=5, fontweight="medium",
            path_effects=[matplotlib.patheffects.withStroke(linewidth=3, foreground="white")])
class_legend(ax, loc="lower right", fs=8.5)
both(fig, "baltic")

# islands in lakes on islands: Newfoundland and Luzon
nest = R["nest"]["top"]
fig, axs = plt.subplots(1, 3, figsize=(13, 5), facecolor=BG)
closeup(axs[0], -59.6, 46.6, -52.5, 51.7, title="Newfoundland")
closeup(axs[1], -58.2, 48.45, -56.95, 49.25, title="Grand Lake")
closeup(axs[2], 120.75, 13.75, 121.25, 14.25, title="Taal Lake, Luzon")
g0 = nest[0]
k0 = np.cos(np.radians(49))
axs[0].add_patch(plt.Rectangle((-58.2 * k0, 48.45), (1.25) * k0, .8, fill=False, ec=HOT, lw=1.6, zorder=6))
axs[1].annotate(f"Glover Island\n{g0['area']:.0f} km²", (g0["lon"] * np.cos(np.radians(48.85)), g0["lat"]), xytext=(-57.55 * np.cos(np.radians(48.85)), 48.55),
                fontsize=10, color=FG, arrowprops=dict(arrowstyle="-", color=FG, lw=.8), zorder=7)
t = [d for d in nest if d["on_name"] == "Luzon" and 13.9 < d["lat"] < 14.1][0]
axs[2].annotate(f"Volcano Island\n{t['area']:.0f} km²", (t["lon"] * np.cos(np.radians(14)), t["lat"]), xytext=(120.79 * np.cos(np.radians(14)), 13.8),
                fontsize=10, color=FG, arrowprops=dict(arrowstyle="-", color=FG, lw=.8), zorder=7)
fig.tight_layout()
both(fig, "nested")

# ---------- header card ----------
fig = plt.figure(figsize=(12, 6.3), facecolor=BG)
ax = fig.add_axes([.27, .02, .73, .96]); ax.set_facecolor(BG)
draw_land(ax, fc="#E9E5DC", ec="#E9E5DC"); show_raster(ax, ras, WEXT); frame(ax, WEXT)
fig.text(.035, .80, "Where the", fontproperties=DISP, fontsize=40, color=FG, va="center")
fig.text(.035, .69, "world's", fontproperties=DISP, fontsize=40, color=FG, va="center")
fig.text(.035, .58, "islands are", fontproperties=DISP, fontsize=40, color=COOL, va="center")
fig.text(.037, .43, f"{fmt(C['n'])} islands in the\nfull-resolution shoreline.\n{R['pop']['pct']:.1f}% of people live\non one.", family=MONO, fontsize=12.5, color=FG, va="top", linespacing=1.5)
fig.text(.037, .07, "maps.tristanhotham.com/world-islands", family=MONO, fontsize=10, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
from PIL import Image
im = Image.open(os.path.join(ROOT, "header.png")); print("header", im.size)
print("figures done")
