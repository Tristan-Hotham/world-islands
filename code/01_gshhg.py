"""Read the GSHHG full-resolution shorelines and build the island list.
Every level-1 polygon that is not one of the five continents (Eurasia, Africa, North America, South America, Australia:
the land polygons of 5 million km2 or more) is a sea island; every level-3 polygon is an island in a lake; level-5
polygons other than the Antarctic continent are Antarctic islands (GSHHG keeps Antarctica apart, at its ice front).
Pieces cut at the date line (ids ending -E/-W) are joined. Each lake gets its parent land, each lake island its lake.
Also counts islands by size at the five GSHHG resolutions (from the meta files alone).
Output: WORK/polys.pkl (geometries, lon/lat), WORK/polys.json (attributes), WORK/resolutions.json."""
import pickle
from collections import Counter, defaultdict
import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.strtree import STRtree
from common import *

CONT_KM2 = 5e6
rows = read_meta("f")
print("rows", len(rows), Counter(r[0] for r in rows))
parts = defaultdict(list)
info = {}
with open(os.path.join(COAST, "gshhs_f.dat"), "rb") as dat:
    for typ, area, npts, south, north, off, nb, pid in rows:
        dat.seek(off)
        b = np.frombuffer(dat.read(nb), dtype="<f4").astype("f8").reshape(npts, 2)
        g = Polygon(b)
        if not g.is_valid:
            g = shapely.make_valid(g)
            g = shapely.union_all([p for p in getattr(g, "geoms", [g]) if p.geom_type in ("Polygon", "MultiPolygon")])
        bid = base_id(pid)
        parts[bid].append(g)
        info[bid] = (typ, area, info.get(bid, (0, 0, 0))[2] + npts)

polys, geoms = [], []
for bid, gs in parts.items():
    typ, area, npts = info[bid]
    g = gs[0] if len(gs) == 1 else shapely.union_all(gs)
    if typ == 1:
        kind = "continent" if area >= CONT_KM2 else "sea"
    elif typ == 2:
        kind = "lake"
    elif typ == 3:
        kind = "lakeisl"
    elif typ == 5:
        kind = "antcont" if area >= CONT_KM2 else "ant"
    else:
        kind = "other"
    rp = g.representative_point()
    polys.append({"id": bid, "lvl": typ, "kind": kind, "area": area, "npts": npts, "split": len(gs) > 1,
                  "lon": round(rp.x, 5), "lat": round(rp.y, 5), "bounds": [round(v, 5) for v in g.bounds]})
    geoms.append(g)
print("polygons", Counter(p["kind"] for p in polys))
cont = sorted([(p["area"], p["id"]) for p in polys if p["kind"] in ("continent", "antcont")], reverse=True)
print("continents", cont)
assert len([c for c in cont]) == 6, cont

# parents: lake -> land polygon (level 1 or 5), lake island -> lake
lvl = np.array([p["lvl"] for p in polys])
area = np.array([p["area"] for p in polys])
pts = shapely.points([(p["lon"], p["lat"]) for p in polys])
for child, parent_lv in ((2, (1, 5)), (3, (2,))):
    pidx = np.where(np.isin(lvl, parent_lv))[0]
    tree = STRtree([geoms[i] for i in pidx])
    cidx = np.where(lvl == child)[0]
    a, b = tree.query(pts[cidx], predicate="within")
    best = {}
    for ci, pj in zip(a, b):
        i, j = cidx[ci], pidx[pj]
        if i not in best or area[j] < area[best[i]]:
            best[i] = j
    miss = 0
    for i in cidx:
        if i in best:
            polys[i]["parent"] = polys[best[i]]["id"]
        else:
            miss += 1
    print("level", child, "with parent", len(best), "missing", miss)

pickle.dump([shapely.to_wkb(g) for g in geoms], open(f"{WORK}/polys.pkl", "wb"))
jsave(polys, f"{WORK}/polys.json")

# island counts at every GSHHG resolution, from the meta files (areas are GSHHG's own)
RES = {}
for res in ("c", "l", "i", "h", "f"):
    rr = read_meta(res)
    seen = {}
    for typ, a, npts, s, n, off, nb, pid in rr:
        seen[(typ, base_id(pid))] = (typ, a)
    isl = [a for (typ, a) in seen.values() if (typ == 1 and a < CONT_KM2) or typ == 3 or (typ == 5 and a < CONT_KM2)]
    sea = [a for (typ, a) in seen.values() if typ == 1 and a < CONT_KM2]
    RES[res] = {"n_all": len(isl), "n_sea": len(sea), "n_lakeisl": sum(1 for (t, a) in seen.values() if t == 3),
                "n_ant": sum(1 for (t, a) in seen.values() if t == 5 and a < CONT_KM2),
                "n_lakes": sum(1 for (t, a) in seen.values() if t == 2),
                "ge": {str(th): sum(1 for a in isl if a >= th) for th in (0.1, 1, 10, 100, 1000)},
                "min_area": min(isl)}
    print(res, RES[res])
jsave(RES, f"{WORK}/resolutions.json")
