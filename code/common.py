"""Shared paths and helpers for the world-islands project.

Raw inputs (read in place, never modified):
  /home/claude/newdata/raw2/coast/gshhs_f.dat, gshhsmeta_f.dat
      GSHHG 2.3 full-resolution shorelines (Wessel and Smith; LGPL-3.0), as packaged in the basemap-data-hires 2.0.0
      Python package (pip install basemap-data-hires; files in mpl_toolkits/basemap_data/). Binary little-endian float32
      lon/lat pairs; the meta file lists, per polygon: level (1 land, 2 lake, 3 island in a lake, 5 Antarctica and its
      islands at the ice front), area km2, points, south, north, byte offset, bytes, id (polygons cut at the date line
      carry -E and -W suffixes).
  $WI_RAW/gshhg/gshhsmeta_{h,i,l,c}.dat
      The coarser GSHHG resolutions (high, intermediate, low, crude) from basemap-data-hires and basemap-data 2.0.0 (pip),
      used only for the island count at each resolution.
  $WI_RAW/wp/L3/*.bin.gz, _meta.json
      WorldPop Global 2 (R2024B) constrained population, 2025 estimate, at 30 arc seconds (about 1 km), CC BY 4.0, as
      re-tiled by https://github.com/nn0000asdf/world-population-3d (docs/tiles/L3, MIT): 957 tiles of 5 degrees, each
      holding the populated cells (3 or more people) with log-quantised counts (relative error under 0.05%).
  $WI_RAW/ne_10m_geography_regions_polys.geojson, ne_10m_geography_regions_points.geojson
      Natural Earth 10m physical labels (public domain), from github.com/nvkelso/natural-earth-vector (island names).
  /home/claude/newdata/raw2/coast/ne_10m_land.geojson, ne_10m_minor_islands.geojson   Natural Earth 10m land and minor islands
  /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson      Natural Earth 10m countries (public domain)
  /home/claude/newdata/raw/geo/ne_50m_admin_0_countries.geojson      Natural Earth 50m countries (outlines for figures)
  /home/claude/newdata/raw/geo/ne_10m_populated_places_simple.geojson Natural Earth populated places (names on the map)
"""
import json, gzip, math, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COAST = os.environ.get("WI_COAST", "/home/claude/newdata/raw2/coast")
GEO = os.environ.get("WI_GEO", "/home/claude/newdata/raw/geo")
RAW = os.environ.get("WI_RAW", "/dev/shm/wi/raw")          # fetched from GitHub and PyPI (see README)
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("WITMP", "/dev/shm/wi"), "work")   # intermediates live in memory, not in the repo
FONTS = os.environ.get("WI_FONTS", "/home/claude/ref/fonts")
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "world-islands"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23848301"             # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/world-islands/"       # filled in by the publisher
RETRIEVED = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

CONTINENT_IDS = {"0": "Eurasia", "1": "Africa", "2": "North America", "3": "South America", "6": "Australia", "4": "Antarctica"}
# size classes (km2) for the map and the counts
CLASSES = [("c0", "Under 0.1 km²", 0, 0.1), ("c1", "0.1 to 1 km²", 0.1, 1), ("c2", "1 to 10 km²", 1, 10),
           ("c3", "10 to 100 km²", 10, 100), ("c4", "100 to 1,000 km²", 100, 1000), ("c5", "1,000 to 10,000 km²", 1000, 1e4),
           ("c6", "10,000 to 100,000 km²", 1e4, 1e5), ("c7", "100,000 km² and over", 1e5, 1e12)]
CLASS_COL = ["#F5C842", "#EE9A35", "#E06B3C", "#C9455A", "#A8357E", "#84389A", "#5B3E9E", "#34409A"]   # sequential: light gold (tiny) to indigo (huge)
REGIONS = [("eur", "Europe"), ("asia", "Asia"), ("afr", "Africa"), ("nam", "North America"), ("car", "Caribbean and Central America"),
           ("sam", "South America"), ("oce", "Oceania"), ("ant", "Antarctica and the far south")]


def size_class(a):
    for i, (k, l, lo, hi) in enumerate(CLASSES):
        if lo <= a < hi:
            return i
    return len(CLASSES) - 1


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def rnd(v):
    """Round half up (so 32.5 shows as 33 everywhere, as in the page's JavaScript)."""
    return int(math.floor(float(v) + 0.5))


def read_meta(res):
    """Rows of a GSHHG meta file: (level, area, npts, south, north, offset, nbytes, id)."""
    path = os.path.join(COAST, "gshhsmeta_f.dat") if res == "f" else os.path.join(RAW, "gshhg", f"gshhsmeta_{res}.dat")
    out = []
    with open(path) as f:
        for ln in f:
            t = ln.split()
            out.append((int(t[0]), float(t[1]), int(t[2]), float(t[3]), float(t[4]), int(t[5]), int(t[6]), t[7]))
    return out


def base_id(pid):
    return pid[:-2] if pid.endswith("-E") or pid.endswith("-W") else pid
