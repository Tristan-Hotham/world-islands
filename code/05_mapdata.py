"""Page data: raster tiles of every island coloured by size (zoom 1 to 6, web mercator, only tiles with land), points for
every island (for clicks and the close-up dots), simplified outlines of islands of 100 km2 or more, country borders
and place names. Output: tiles/{z}/{x}/{y}.png, data/tiles.json, data/points.json, data/outlines.geojson,
data/world.json, data/cities.json, data/site.json."""
import pickle
import numpy as np
import shapely
from shapely import set_precision
from shapely.geometry import shape
from rasterio import features
from rasterio.transform import Affine
from PIL import Image
from common import *

F = jload(f"{WORK}/isl_final.json")
I, CROW, CN = F["islands"], F["countries"], F["cname"]
G = [shapely.from_wkb(b) for b in pickle.load(open(f"{WORK}/polys.pkl", "rb"))]
TILES = os.path.join(ROOT, "tiles")
MAXLAT = 85.05112878


def merc(g):
    """lon/lat geometry to unit web mercator (x, y in 0..1, y down)."""
    def f(a):
        lon = a[:, 0]; lat = np.clip(a[:, 1], -MAXLAT, MAXLAT)
        s = np.sin(np.radians(lat))
        return np.column_stack([(lon + 180) / 360, .5 - np.log((1 + s) / (1 - s)) / (4 * np.pi)])
    return shapely.transform(g, f)


order = sorted(range(len(I)), key=lambda k: -I[k]["area"])          # big first; small drawn on top
MG = [merc(G[I[k]["i"]]) for k in order]
CLS = [I[k]["cls"] + 1 for k in order]
from shapely.strtree import STRtree
GW = {I[k]["i"] for k in order if I[k]["area"] >= 100}
G = {i: G[i] for i in GW}                     # keep lon/lat outlines only for the big islands (memory)
MT = STRtree(MG)
pal = [0, 0, 0]
for h in CLASS_COL:
    pal += [int(h[i:i + 2], 16) for i in (1, 3, 5)]
pal += [0, 0, 0] * (256 - len(pal) // 3)
idx = {}
for z in (range(1, 7) if os.environ.get("WI_TILES") or not os.path.exists(f"{TILES}/6") else []):
    nt = 2 ** z; n = 0
    blk = min(nt, 8)                           # rasterise blocks of up to 8 x 8 tiles
    for by in range(0, nt, blk):
        for bx in range(0, nt, blk):
            box = (bx / nt, by / nt, (bx + blk) / nt, (by + blk) / nt)
            hit = sorted(MT.query(shapely.box(*box)))      # indices follow 'order': big first
            if not len(hit):
                continue
            W = 256 * blk
            tr = Affine((box[2] - box[0]) / W, 0, box[0], 0, (box[3] - box[1]) / W, box[1])
            ras = np.zeros((W, W), dtype=np.uint8)
            shp = ((shapely.clip_by_rect(MG[j], *box) if shapely.get_num_coordinates(MG[j]) > 2000 else MG[j], CLS[j]) for j in hit)
            features.rasterize(((g, v) for g, v in shp if not g.is_empty), out=ras, transform=tr, all_touched=True)
            for ty in range(blk):
                for tx in range(blk):
                    t = ras[ty * 256:(ty + 1) * 256, tx * 256:(tx + 1) * 256]
                    if not t.any():
                        continue
                    X, Y = bx + tx, by + ty
                    im = Image.fromarray(t, mode="P"); im.putpalette(pal)
                    os.makedirs(f"{TILES}/{z}/{X}", exist_ok=True)
                    im.save(f"{TILES}/{z}/{X}/{Y}.png", transparency=0, optimize=True)
                    idx.setdefault(str(z), []).append(X * nt + Y); n += 1
    print("zoom", z, n, "tiles", flush=True)
if idx:
    jsave(idx, f"{DATA}/tiles.json")

# points for every island, sorted by area (so rank by area = position + 1)
I.sort(key=lambda o: -o["area"])
cl = sorted({o["c"] for o in I})
ci = {c: k for k, c in enumerate(cl)}
names = []
P = {"x": [], "y": [], "a": [], "p": [], "c": [], "k": [], "n": [], "pl": []}
places = []
for o in I:
    P["x"].append(round(o["lon"] * 1000)); P["y"].append(round(o["lat"] * 1000))
    a = o["area"]
    P["a"].append(float(f"{a:.3g}") if a < 1000 else round(a))
    P["p"].append(rnd(o["pop"])); P["c"].append(ci[o["c"]])
    P["k"].append({"sea": 0, "lakeisl": 1, "ant": 2}[o["kind"]])
    if o["name"]:
        P["n"].append(len(names)); names.append(dash(o["name"]))
    else:
        P["n"].append(-1)
    if o.get("place"):
        P["pl"].append(len(places)); places.append(o["place"])
    else:
        P["pl"].append(-1)
P["names"] = names; P["places"] = places
jsave(P, f"{DATA}/points.json")
print("points.json", os.path.getsize(f"{DATA}/points.json") // 1024, "KB", len(names), "names")

# outlines of islands of 100 km2 or more
feats = []
for k, o in enumerate(I):
    if o["area"] < 100:
        break
    g = G[o["i"]]
    tol = 0.02 if o["area"] > 2e4 else 0.01 if o["area"] > 1000 else 0.005
    g = set_precision(g.simplify(tol, preserve_topology=True), 0.001)
    if g.is_empty:
        continue
    feats.append({"type": "Feature", "properties": {"r": k}, "geometry": json.loads(json.dumps(g.__geo_interface__))})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/outlines.geojson")
print("outlines", len(feats), os.path.getsize(f"{DATA}/outlines.geojson") // 1024, "KB")

# borders
NE = jload(os.path.join(GEO, "ne_50m_admin_0_countries.geojson"))
wf = []
for f in NE["features"]:
    if f["properties"]["ADM0_A3"] in ("IOA", "ATC"):      # scattered specks whose simplified outline becomes a box
        continue
    g = set_precision(shape(f["geometry"]).simplify(0.03, preserve_topology=True), 0.01)
    wf.append({"type": "Feature", "properties": {"iso": f["properties"]["ADM0_A3"]}, "geometry": json.loads(json.dumps(g.__geo_interface__))})
jsave({"type": "FeatureCollection", "features": wf}, f"{DATA}/world.json")
print("world.json", os.path.getsize(f"{DATA}/world.json") // 1024, "KB")

# place names
PP = jload(os.path.join(GEO, "ne_10m_populated_places_simple.geojson"))
cities = []
for f in PP["features"]:
    p = f["properties"]
    if p["pop_max"] >= 100000 or p["adm0cap"] or p["featurecla"].startswith("Admin-0"):
        cities.append({"name": p["name"], "lon": round(p["longitude"], 3), "lat": round(p["latitude"], 3), "pop": p["pop_max"],
                       "cap": 1 if p["adm0cap"] else 0, "iso": p["adm0_a3"]})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")
print("cities", len(cities))

# country list for search and the side panel
site = {"countries": cl, "cname": {c: CN.get(c, c) for c in cl}, "class_labels": [c[1] for c in CLASSES], "class_col": CLASS_COL,
        "regions": REGIONS,
        "cstats": {d["c"]: [d["n"], d["ge1"], d["ge10"], round(d["area"]), rnd(d["people"]), rnd(d["people_isl"]),
                            d["largest"]["name"] if d["largest"] else "", d["most_pop"]["name"] if d["most_pop"] else "", d["bbox"]]
                   for d in CROW if d["n"]}}
jsave(site, f"{DATA}/site.json")
