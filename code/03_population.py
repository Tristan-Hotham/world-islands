"""Population of every island and continent from WorldPop Global 2 (2025, constrained, 30 arc seconds).
For each 5-degree WorldPop tile the GSHHG land polygons (continents, sea islands, islands in lakes, Antarctica) are burned
into a grid aligned with the population cells (a cell belongs to the polygon under its centre; lakes are left empty).
Coastal cells whose centre is in the sea or a lake go to a polygon that touches them, else to the nearest land cell
within 2 cells (about 2 km); the rest are counted as unplaced. Each cell also gets its Natural Earth 10m country, for
national totals. Output: WORK/pop.json (people per polygon index; people and people on islands per country)."""
import gzip, struct, pickle, time, warnings
warnings.filterwarnings("ignore")
from collections import defaultdict
import numpy as np
import shapely
from shapely.strtree import STRtree
from shapely.geometry import shape
from rasterio import features
from rasterio.transform import from_origin
from scipy import ndimage
from common import *

P = jload(f"{WORK}/polys.json")
G = [shapely.from_wkb(b) for b in pickle.load(open(f"{WORK}/polys.pkl", "rb"))]
land = [i for i, p in enumerate(P) if p["lvl"] in (1, 3, 5)]
lakes = [i for i, p in enumerate(P) if p["lvl"] == 2]
ltree = STRtree([G[i] for i in land]); ktree = STRtree([G[i] for i in lakes])
area = np.array([p["area"] for p in P])
META = jload(os.path.join(RAW, "wp", "L3", "_meta.json"))
CELL = META["cell"]; TD = META["tileDeg"]; NPX = round(TD / CELL)


def read_tile(name):
    b = gzip.open(os.path.join(RAW, "wp", "L3", name + ".bin.gz")).read()
    magic, nx, ny, cell, w, n, pmax, cnt = struct.unpack("<4sHHffffI", b[:28])
    assert magic == b"POPB" and nx == NPX
    o = 28
    ix = np.frombuffer(b, "<u2", cnt, o); o += 2 * cnt
    iy = np.frombuffer(b, "<u2", cnt, o); o += 2 * cnt
    q = np.frombuffer(b, "<u2", cnt, o)
    lp = np.log10(pmax) if pmax > 1 else 1e-6
    pop = 10 ** (q.astype("f8") / 65535 * lp)
    return ix.astype(int), iy.astype(int), pop, w, n


def clip(g, box):
    return shapely.clip_by_rect(g, *box) if len(shapely.get_coordinates(g)) > 3000 else g


NE = jload(os.path.join(GEO, "ne_10m_admin_0_countries.geojson"))
CG = [shape(f["geometry"]).buffer(0) for f in NE["features"]]
CISO = [f["properties"]["ADM0_A3"] for f in NE["features"]]
ctree = STRtree(CG)
ISLAND_IDX = np.array([i for i, p in enumerate(P) if p["kind"] in ("sea", "lakeisl", "ant")])
cpop = defaultdict(lambda: [0.0, 0.0])      # country: [all people, people on islands]
pop = defaultdict(float)
stat = {"total": 0.0, "direct": 0.0, "touch": 0.0, "near": 0.0, "unplaced": 0.0, "cells": 0, "tiles": 0}
t0 = time.time()
names = sorted(META["tiles"])
for k, name in enumerate(names):
    ix, iy, pp, w, n = read_tile(name)
    w, n = round(w, 4), round(n, 4)
    box = (w, n - TD, w + TD, n)
    tb = shapely.box(*box)
    tr = from_origin(w, n, CELL, CELL)
    li = [land[j] for j in ltree.query(tb)]
    li.sort(key=lambda i: -area[i])          # big first, so islands in lakes and small islands sit on top
    grid = np.zeros((NPX, NPX), dtype=np.int32)
    shp = [(clip(G[i], box), i + 1) for i in li if P[i]["lvl"] == 1 or P[i]["lvl"] == 5]
    if shp:
        features.rasterize(shp, out=grid, transform=tr)
    kk = [lakes[j] for j in ktree.query(tb)]
    if kk:
        features.rasterize([(clip(G[i], box), 0) for i in kk], out=grid, transform=tr)
    shp3 = [(clip(G[i], box), i + 1) for i in li if P[i]["lvl"] == 3]
    if shp3:
        features.rasterize(shp3, out=grid, transform=tr)
    v = grid[iy, ix].astype(np.int64) - 1          # polygon index per populated cell, -1 if none yet
    stat["total"] += pp.sum(); stat["cells"] += len(pp); stat["tiles"] += 1
    stat["direct"] += pp[v >= 0].sum()
    miss = np.nonzero(v < 0)[0]
    if len(miss):
        # polygons touching the cell (small islands, atolls and spits narrower than a cell)
        touch = np.zeros((NPX, NPX), dtype=np.int32)
        features.rasterize([(clip(G[i], box), i + 1) for i in li], out=touch, transform=tr, all_touched=True)
        tv = touch[iy[miss], ix[miss]].astype(np.int64) - 1
        v[miss] = tv
        stat["touch"] += pp[miss[tv >= 0]].sum()
        rest = miss[tv < 0]
        if len(rest):
            d, (ry, rx) = ndimage.distance_transform_edt(grid == 0, return_indices=True)
            y, x = iy[rest], ix[rest]
            near = d[y, x] <= 2.0
            v[rest[near]] = grid[ry[y[near], x[near]], rx[y[near], x[near]]].astype(np.int64) - 1
            stat["near"] += pp[rest[near]].sum(); stat["unplaced"] += pp[rest[~near]].sum()
    ok = v >= 0
    sums = np.bincount(v[ok], weights=pp[ok])
    for vid in np.nonzero(sums)[0]:
        pop[int(vid)] += sums[vid]
    # country of every cell (Natural Earth 10m; cells off the country outlines go to the nearest country cell)
    ci = [j for j in ctree.query(tb)]
    cgrid = np.zeros((NPX, NPX), dtype=np.int32)
    if ci:
        features.rasterize([(clip(CG[j], box), j + 1) for j in ci], out=cgrid, transform=tr)
    cv = cgrid[iy, ix].astype(np.int64) - 1
    if (cv < 0).any():
        if ci and (cgrid > 0).any():
            d, (ry, rx) = ndimage.distance_transform_edt(cgrid == 0, return_indices=True)
            m = cv < 0
            cv[m] = cgrid[ry[iy[m], ix[m]], rx[iy[m], ix[m]]].astype(np.int64) - 1
        if (cv < 0).any():       # a tile with people but no country outline: the nearest country to its cells
            m = np.nonzero(cv < 0)[0]
            pts_ = shapely.points(w + (ix[m] + .5) * CELL, n - (iy[m] + .5) * CELL)
            cv[m] = ctree.query_nearest(pts_, all_matches=False)[1]
    onisl = ok & np.isin(v, ISLAND_IDX)
    for flag, arr in ((0, np.ones(len(pp), bool)), (1, onisl)):
        s2 = np.bincount(cv[arr], weights=pp[arr], minlength=len(CG))
        for j in np.nonzero(s2)[0]:
            cpop[int(j)][flag] += s2[j]
    if k % 50 == 0:
        print(k, name, f"{stat['total'] / 1e9:.3f} bn", f"{time.time() - t0:.0f}s", flush=True)
print({k: (round(v / 1e6, 2) if isinstance(v, float) else v) for k, v in stat.items()})
stat = {k: float(v) for k, v in stat.items()}
jsave({"pop": {str(k): round(v, 1) for k, v in pop.items()}, "stat": stat,
       "country": {CISO[j]: [round(a, 1), round(b, 1)] for j, (a, b) in cpop.items()}}, f"{WORK}/pop.json")
