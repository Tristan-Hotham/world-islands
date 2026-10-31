"""Country, region and name for every island.
Country: the Natural Earth 10m admin-0 unit under the island's representative point, else the nearest one (distance
kept, in km). For islands of 1,000 km2 or more, the share of the island in each country (shared islands such as Borneo,
New Guinea, Hispaniola, Ireland, Timor and Tierra del Fuego). Region: from the country's Natural Earth continent and
subregion, with geographic exceptions for far-flung parts (Hawaii, Easter Island, the French and Dutch Caribbean,
Reunion and Mayotte, Asian Russia, New Guinea). Name: Natural Earth 10m physical labels (island polygons and points);
largest Natural Earth populated place on the island, kept for the popups.
Output: WORK/islands.json."""
import pickle
from collections import Counter, defaultdict
import numpy as np
import shapely
from shapely.geometry import shape
from shapely.strtree import STRtree
from shapely.ops import nearest_points
from pyproj import Geod
from common import *

GEOD = Geod(ellps="WGS84")
P = jload(f"{WORK}/polys.json")
G = [shapely.from_wkb(b) for b in pickle.load(open(f"{WORK}/polys.pkl", "rb"))]
ISL_KINDS = ("sea", "lakeisl", "ant")
idx = [i for i, p in enumerate(P) if p["kind"] in ISL_KINDS]
print("islands", len(idx))

NE = jload(os.path.join(GEO, "ne_10m_admin_0_countries.geojson"))
CG, CP = [], []
for f in NE["features"]:
    CG.append(shape(f["geometry"]).buffer(0)); CP.append(f["properties"])
ctree = STRtree(CG)
pts = shapely.points([(P[i]["lon"], P[i]["lat"]) for i in idx])
a, b = ctree.query(pts, predicate="within")
cty = {}
for ii, j in zip(a, b):
    cty.setdefault(ii, j)
miss = [ii for ii in range(len(idx)) if ii not in cty]
print("in a country", len(cty), "not", len(miss))
near_d = {}
if miss:
    mi, mj = ctree.query_nearest(pts[miss], return_distance=False, all_matches=False)
    for k, j in zip(mi, mj):
        ii = miss[k]; cty[ii] = j
        q = pts[ii]; npnt = nearest_points(CG[j], q)[0]
        near_d[ii] = GEOD.inv(q.x, q.y, npnt.x, npnt.y)[2] / 1000

SEVEN = {"SYC": "afr", "MUS": "afr", "SHN": "afr", "MDV": "asia", "IOT": "asia", "ATF": "ant", "HMD": "ant", "SGS": "ant", "CLP": "car", "ATA": "ant"}
CONT = {"Europe": "eur", "Asia": "asia", "Africa": "afr", "South America": "sam", "Oceania": "oce", "Antarctica": "ant"}


def region(cp, lon, lat):
    iso = cp["ADM0_A3"]
    if iso in SEVEN:
        return SEVEN[iso]
    c = cp["CONTINENT"]
    if iso == "FRA":
        if lon < -40: return "car" if lat > 10 else "sam"
        if lon > 30 and lat < 0: return "afr"
    if iso == "NLD" and lon < -30: return "car"
    if iso == "USA" and lon < -150 and lat < 30: return "oce"
    if iso == "CHL" and lon < -100: return "oce"
    if iso == "RUS" and lon > 68: return "asia"
    if iso in ("AUS", "NZL", "NOR") and lat < -50: return "ant"
    if c == "North America":
        return "car" if cp["SUBREGION"] in ("Caribbean", "Central America") else "nam"
    return CONT.get(c, "ant" if lat < -50 else "oce")


NAMEFIX = {"GBR": "United Kingdom", "USA": "United States", "CZE": "Czechia", "MKD": "North Macedonia"}
out = []
for ii, i in enumerate(idx):
    p = P[i]; cp = CP[cty[ii]]
    if p["kind"] == "ant":
        iso, cname, reg = "ATA", "Antarctica", "ant"
        cp = next(c for c in CP if c["ADM0_A3"] == "ATA")
    else:
        iso = cp["ADM0_A3"]; reg = region(cp, p["lon"], p["lat"])
    out.append({"i": i, "id": p["id"], "kind": p["kind"], "area": p["area"], "lon": p["lon"], "lat": p["lat"],
                "c": iso, "sov": cp["SOV_A3"], "r": reg, "near_km": round(near_d.get(ii, 0), 1)})

# shares of big islands in each country (equal-area: geodesic area of the intersection)
cg_s = {}
for o in out:
    if o["area"] < 1000 or o["kind"] == "ant":
        continue
    g = G[o["i"]].simplify(0.005, preserve_topology=True)
    sh = []
    for j in ctree.query(g, predicate="intersects"):
        inter = g.intersection(CG[j])
        if inter.is_empty:
            continue
        ar = abs(GEOD.geometry_area_perimeter(inter)[0]) / 1e6
        if ar > 0.5:
            sh.append([CP[j]["ADM0_A3"], ar])
    tot = sum(x[1] for x in sh) or 1
    sh = sorted([[c, round(100 * x / tot, 1)] for c, x in sh], key=lambda t: -t[1])
    sh = [x for x in sh if x[1] >= 0.5]
    o["shares"] = sh
    if sh and sh[0][0] != o["c"]:
        cp = next(c for c in CP if c["ADM0_A3"] == sh[0][0])
        o["c"] = sh[0][0]; o["sov"] = cp["SOV_A3"]; o["r"] = region(cp, o["lon"], o["lat"])
print("shared big islands", [(o["id"], o["shares"]) for o in out if len(o.get("shares", [])) > 1])

# names from Natural Earth physical labels
NR = jload(os.path.join(RAW, "ne_10m_geography_regions_polys.geojson"))
NP = jload(os.path.join(RAW, "ne_10m_geography_regions_points.geojson"))
iidx = {o["i"]: k for k, o in enumerate(out)}
itree = STRtree([G[o["i"]] for o in out])
cand = defaultdict(list)
for f in NR["features"]:
    pr = f["properties"]
    if pr["FEATURECLA"] != "Island":
        continue
    g = shape(f["geometry"]).buffer(0)
    nm = pr.get("NAME_EN") or pr["NAME"]
    best = None
    for k in itree.query(g, predicate="intersects"):
        gi = G[out[k]["i"]]
        ov = gi.intersection(g).area
        if best is None or ov > best[1]:
            best = (k, ov)
    if best and best[1] > 0:
        cand[best[0]].append((best[1], nm, pr.get("WIKIDATAID")))
for f in NP["features"]:
    pr = f["properties"]
    if str(pr.get("featurecla", "")).lower() != "island":
        continue
    pt = shape(f["geometry"])
    hit = list(itree.query(pt, predicate="intersects"))
    if not hit:
        k = itree.nearest(pt)
        if G[out[k]["i"]].distance(pt) > 0.05:
            continue
        hit = [k]
    k = min(hit, key=lambda k: out[k]["area"])
    cand[k].append((0, pr.get("name_en") or pr.get("name"), pr.get("wikidataid")))
for k, cs in cand.items():
    cs.sort(key=lambda t: -t[0])
    out[k]["name"] = cs[0][1].replace(" Island", "") if cs[0][1].endswith(" Island") and len(cs[0][1]) > 12 else cs[0][1]
    out[k]["wd"] = cs[0][2]
print("named", sum(1 for o in out if o.get("name")))

# largest Natural Earth populated place on each island
PP = jload(os.path.join(GEO, "ne_10m_populated_places_simple.geojson"))
for f in PP["features"]:
    pr = f["properties"]
    pt = shapely.Point(pr["longitude"], pr["latitude"])
    hit = list(itree.query(pt, predicate="intersects"))
    if not hit:
        k = itree.nearest(pt)
        if G[out[k]["i"]].distance(pt) > 0.02:
            continue
        hit = [k]
    k = min(hit, key=lambda k: out[k]["area"])
    o = out[k]
    if pr["pop_max"] > o.get("place_pop", -1):
        o["place"] = pr["name"]; o["place_pop"] = pr["pop_max"]
    o["n_places"] = o.get("n_places", 0) + 1
print("islands with a place", sum(1 for o in out if o.get("place")))
CN = {c["ADM0_A3"]: NAMEFIX.get(c["ADM0_A3"], c["NAME"]) for c in CP}
SOVN = {c["SOV_A3"]: c["SOVEREIGNT"] for c in CP}
POP = {c["ADM0_A3"]: c["POP_EST"] for c in CP}
jsave({"islands": out, "cname": CN, "sovname": SOVN, "pop_est": POP,
       "cont": {c["ADM0_A3"]: c["CONTINENT"] for c in CP}}, f"{WORK}/islands.json")
print(Counter(o["r"] for o in out))
print(Counter(o["c"] for o in out).most_common(15))
