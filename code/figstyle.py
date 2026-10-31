"""House style for static figures: fonts (static Fraunces instances cut from the variable font in /home/claude/ref/fonts,
written to WORK), the paper-and-sea palette, Natural Earth land in the Equal Earth projection, and a raster of every
island coloured by size class (cached in WORK)."""
import pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
from matplotlib.colors import ListedColormap
import numpy as np
import shapely
from shapely.geometry import shape
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold"), (600, "Semi")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#5E6A70", "axes.labelcolor": "#1D2A31",
                     "xtick.color": "#5E6A70", "ytick.color": "#5E6A70"})
# paper, ink, muted, land, rule, sea
BG, FG, MUT, LAND, RULE, SEA = "#F6F3EC", "#1D2A31", "#5E6A70", "#E2DDD2", "#DCD5C6", "#EAF0F0"
HOT, COOL, GOLD = "#C9455A", "#34409A", "#E09A2E"
CMAP = ListedColormap(CLASS_COL)
CUT = 11 - 180
EQ = Transformer.from_crs(4326, "+proj=eqearth +lon_0=11 +datum=WGS84", always_xy=True)
INV = Transformer.from_crs("+proj=eqearth +lon_0=11 +datum=WGS84", 4326, always_xy=True)


def proj(g):
    return shapely.transform(g, lambda a: np.column_stack(EQ.transform(a[:, 0], a[:, 1])))


def to_xy(lon, lat):
    return EQ.transform(lon, lat)


NE = jload(os.path.join(GEO, "ne_50m_admin_0_countries.geojson"))
LANDP = []
for f in NE["features"]:
    g = shape(f["geometry"])
    for p0 in getattr(g, "geoms", [g]):
        b = p0.bounds
        pp = [shapely.clip_by_rect(p0, -180, -90, CUT - 1e-6, 90), shapely.clip_by_rect(p0, CUT + 1e-6, -90, 180, 90)] if b[0] < CUT < b[2] else [p0]
        for q in pp:
            for p in getattr(q, "geoms", [q]):
                if p.is_empty or p.geom_type != "Polygon":
                    continue
                x, y = EQ.transform(*np.array(p.exterior.coords).T)
                LANDP.append(np.column_stack([x, y]))


def draw_land(ax, fc=LAND, ec="#FFFFFF", lw=.3, z=1):
    for p in LANDP:
        ax.add_patch(MPoly(p, closed=True, fc=fc, ec=ec, lw=lw, zorder=z))


_x = EQ.transform(-168.999, 0)[0]
WEXT = (_x, -_x, EQ.transform(11, -58)[1], EQ.transform(11, 84)[1])


def island_raster(ext=WEXT, width=5200, key="world", minarea=0.0):
    """Class raster (0 = none, 1..8 = size class) of every island inside ext (Equal Earth metres), cached."""
    path = f"{WORK}/ras_{key}_{width}.npy"
    if os.path.exists(path):
        return np.load(path)
    from rasterio import features
    from rasterio.transform import Affine
    F = jload(f"{WORK}/isl_final.json")["islands"]
    G = pickle.load(open(f"{WORK}/polys.pkl", "rb"))
    lo, la = INV.transform([ext[0], ext[1], ext[0], ext[1], (ext[0] + ext[1]) / 2], [ext[2], ext[2], ext[3], ext[3], ext[2]])
    F = sorted([o for o in F if o["area"] >= minarea], key=lambda o: -o["area"])
    H = int(width * (ext[3] - ext[2]) / (ext[1] - ext[0]))
    tr = Affine((ext[1] - ext[0]) / width, 0, ext[0], 0, -(ext[3] - ext[2]) / H, ext[3])
    ras = np.zeros((H, width), dtype=np.uint8)
    box = shapely.box(*INV.transform(ext[0], ext[2]), *INV.transform(ext[1], ext[3])) if key != "world" else None
    shp = []
    for o in F:
        g = shapely.from_wkb(G[o["i"]])
        if box is not None and not g.intersects(box):
            continue
        b = g.bounds
        if b[0] < CUT < b[2]:          # cut at the map's edge so nothing smears across the map
            parts = [shapely.clip_by_rect(g, -180, -90, CUT - 1e-6, 90), shapely.clip_by_rect(g, CUT + 1e-6, -90, 180, 90)]
        else:
            parts = [g]
        for q in parts:
            if not q.is_empty:
                shp.append((proj(q), o["cls"] + 1))
        if len(shp) >= 20000:
            features.rasterize(shp, out=ras, transform=tr, all_touched=True); shp = []
    if shp:
        features.rasterize(shp, out=ras, transform=tr, all_touched=True)
    np.save(path, ras)
    return ras


def show_raster(ax, ras, ext, z=3):
    m = np.ma.masked_equal(ras, 0)
    ax.imshow(m - 1, cmap=CMAP, vmin=-.5, vmax=7.5, extent=(ext[0], ext[1], ext[2], ext[3]), interpolation="nearest", zorder=z)


def frame(ax, ext):
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def save(fig, name, dpi=200):
    fig.savefig(name, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)


def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_facecolor(BG)
