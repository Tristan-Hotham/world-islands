"""All analysis. Joins islands, countries, names and population; counts by size, region and country; rankings by area,
people and density; islands in lakes on islands; the island count at each GSHHG resolution and in Natural Earth.
Writes data/results.json (every number quoted anywhere), data/islands.csv.gz (gzipped CSV), data/countries.csv, data/regions.csv,
data/size_classes.csv, data/resolutions.csv and WORK/isl_final.json (for the maps and figures)."""
import csv, gzip
from collections import Counter, defaultdict
import shapely
from shapely.geometry import shape
from pyproj import Geod
from common import *
from names import NAMES, RENAME

GEOD = Geod(ellps="WGS84")
D = jload(f"{WORK}/islands.json")
I, CN, SOVN = D["islands"], D["cname"], D["sovname"]
POLY = jload(f"{WORK}/polys.json")
PJ = jload(f"{WORK}/pop.json")
POP, CPOP, PST = PJ["pop"], PJ["country"], PJ["stat"]
RES = jload(f"{WORK}/resolutions.json")
RN = dict(REGIONS)
for f in jload(os.path.join(GEO, "ne_10m_admin_0_countries.geojson"))["features"]:
    p = f["properties"]
    CN[p["ADM0_A3"]] = {"GBR": "United Kingdom", "USA": "United States", "CZE": "Czechia", "MKD": "North Macedonia",
                        "RUS": "Russia", "KOR": "South Korea", "PRK": "North Korea", "LAO": "Laos", "CYN": "Northern Cyprus"}.get(p["ADM0_A3"], p["NAME_LONG"])
CN.update({"ATA": "Antarctica", "CYN": "Northern Cyprus", "TWN": "Taiwan", "PSX": "Palestine", "KOS": "Kosovo"})
byid = {p["id"]: p for p in POLY}

for o in I:
    o["pop"] = POP.get(str(o["i"]), 0.0)
    nm = NAMES.get(o["id"]) or o.get("name")
    o["name"] = RENAME.get(nm, nm) if nm else None
    o["cls"] = size_class(o["area"])
    o["dens"] = o["pop"] / o["area"] if o["area"] > 0 else 0
    if o["kind"] == "lakeisl":
        lk = byid[o["id"]] and byid[byid[o["id"]]["parent"]]
        o["lake"] = lk["id"]; o["lake_km2"] = abs(lk["area"]); o["river"] = lk["area"] < 0
        o["lake_on"] = lk.get("parent")
# largest Natural Earth populated place on each island (redone here: a coastal place just off the shoreline goes to the
# biggest island within 0.02 degrees, not to a nearby islet)
import pickle
from shapely.strtree import STRtree
GI = pickle.load(open(f"{WORK}/polys.pkl", "rb"))
IG = [shapely.from_wkb(GI[o["i"]]) for o in I]
itree = STRtree(IG)
for o in I:
    o.pop("place", None); o.pop("place_pop", None)
for f in jload(os.path.join(GEO, "ne_10m_populated_places_simple.geojson"))["features"]:
    pr = f["properties"]; pt = shapely.Point(pr["longitude"], pr["latitude"])
    hit = list(itree.query(pt, predicate="intersects"))
    if hit:
        k = min(hit, key=lambda k: I[k]["area"])
    else:
        near = list(itree.query(pt.buffer(0.02), predicate="intersects"))
        if not near:
            continue
        k = max(near, key=lambda k: I[k]["area"])
    if pr["pop_max"] > I[k].get("place_pop", -1):
        I[k]["place"] = pr["name"]; I[k]["place_pop"] = pr["pop_max"]
del IG, itree, GI
# hand fixes to Natural Earth labels that are not English island names
FIX = {"Chuk-to": "Jeju", "Zanzibar Archipelago": "Unguja (Zanzibar)"}
for o in I:
    if o["name"] in FIX:
        o["name"] = FIX[o["name"]]
EXTRA = {"485": "Singapore", "588": "Batam", "364": "São Luís Island", "468": "Bahrain Island", "762": "Penang Island",
         "358": "Jolo", "528": "Zhoushan Island", "1348": "Xiamen Island", "1752": "Hong Kong Island",
         "187165": "Montreal and Laval (joined in GSHHG)", "1145": "Staten Island", "1095": "Yuhuan Island", "4476": "Muharraq Island",
         "18075": "Betio (Tarawa)", "16837": "Malé", "4580": "Vasilyevsky Island",
         "187162": "Mekong and Bassac river island (as drawn in GSHHG)", "187208": "Glover Island", "187466": "Talim Island",
         "187481": "Volcano Island (Taal)", "187509": "Isla Cabritos"}
for o in I:
    if o["id"] in EXTRA and not o["name"]:
        o["name"] = EXTRA[o["id"]]

I.sort(key=lambda o: -o["area"])
for k, o in enumerate(I):
    o["rank_area"] = k + 1
popd = sorted([o for o in I if o["pop"] >= 0.5], key=lambda o: -o["pop"])
for k, o in enumerate(popd):
    o["rank_pop"] = k + 1
N = len(I)
WORLD_POP = PST["total"]
ISL_POP = sum(o["pop"] for o in I)
cont_area = {cid: byid[cid]["area"] for cid in CONTINENT_IDS}
land_area = sum(p["area"] for p in POLY if p["kind"] in ("sea", "continent", "antcont", "ant"))
isl_area = sum(o["area"] for o in I if o["kind"] in ("sea", "ant"))
r1 = lambda v: None if v is None else round(v, 1)
pc = lambda a, b: 100 * a / b if b else None


def brief(o, extra=()):
    d = {"id": o["id"], "name": o["name"] or "", "c": o["c"], "cname": CN.get(o["c"], o["c"]), "area": round(o["area"], 2),
         "pop": rnd(o["pop"]), "lon": o["lon"], "lat": o["lat"], "kind": o["kind"], "place": o.get("place") or ""}
    for k in extra:
        d[k] = o.get(k)
    return d


R = {"meta": {"retrieved": RETRIEVED, "page": PAGE, "repo": REPO, "worldpop_year": 2025, "n_tiles": PST["tiles"],
              "n_cells": PST["cells"], "cont_km2": 5e6}}
# ---------- counts ----------
ge = lambda th, sel=lambda o: True: sum(1 for o in I if o["area"] >= th and sel(o))
R["counts"] = {
    "n": N, "sea": sum(o["kind"] == "sea" for o in I), "lake": sum(o["kind"] == "lakeisl" for o in I),
    "ant": sum(o["kind"] == "ant" for o in I), "river": sum(1 for o in I if o.get("river")),
    "ge01": ge(0.1), "ge1": ge(1), "ge10": ge(10), "ge100": ge(100), "ge1000": ge(1000), "ge10000": ge(1e4), "ge100000": ge(1e5),
    "ge1_noant": ge(1, lambda o: o["kind"] != "ant"), "ge1_sea": ge(1, lambda o: o["kind"] == "sea"),
    "under01": sum(1 for o in I if o["area"] < 0.1), "under01_pct": pc(sum(1 for o in I if o["area"] < 0.1), N),
    "min_m2": min(o["area"] for o in I) * 1e6, "lakes": sum(1 for p in POLY if p["kind"] == "lake"),
    "isl_area": isl_area, "land_area": land_area, "isl_area_pct": pc(isl_area, land_area),
    "greenland_pct_isl_area": pc(I[0]["area"], isl_area),
    "top10_area_pct": pc(sum(o["area"] for o in I[:10]), isl_area),
    "ge1000_area_pct": pc(sum(o["area"] for o in I if o["area"] >= 1000 and o["kind"] != "lakeisl"), isl_area),
    "under1_area": sum(o["area"] for o in I if o["area"] < 1), "under1_area_pct": pc(sum(o["area"] for o in I if o["area"] < 1), isl_area),
}
cls_rows = []
for k, (key, lab, lo, hi) in enumerate(CLASSES):
    sel = [o for o in I if o["cls"] == k]
    cls_rows.append({"k": key, "label": lab, "n": len(sel), "area": sum(o["area"] for o in sel), "pop": sum(o["pop"] for o in sel),
                     "pct_n": pc(len(sel), N), "pct_area": pc(sum(o["area"] for o in sel), isl_area + sum(o["area"] for o in I if o["kind"] == "lakeisl")),
                     "pct_pop": pc(sum(o["pop"] for o in sel), ISL_POP), "inhabited": sum(1 for o in sel if o["pop"] >= 1)})
R["classes"] = cls_rows

# ---------- resolutions ----------
NEc = {}
for f in ("ne_10m_land", "ne_10m_minor_islands"):
    A = []
    for ft in jload(os.path.join(COAST, f + ".geojson"))["features"]:
        g = shape(ft["geometry"])
        for p in getattr(g, "geoms", [g]):
            A.append(abs(GEOD.geometry_area_perimeter(shapely.Polygon(p.exterior))[0]) / 1e6)
    NEc[f] = [a for a in A if a < 5e6]
nea = NEc["ne_10m_land"] + NEc["ne_10m_minor_islands"]
RL = [("c", "GSHHG crude"), ("l", "GSHHG low"), ("i", "GSHHG intermediate"), ("h", "GSHHG high"), ("f", "GSHHG full")]
res_rows = [{"k": k, "label": l, "n": RES[k]["n_all"], "ge01": RES[k]["ge"]["0.1"], "ge1": RES[k]["ge"]["1"], "ge10": RES[k]["ge"]["10"],
             "ge100": RES[k]["ge"]["100"], "ge1000": RES[k]["ge"]["1000"], "min_km2": RES[k]["min_area"]} for k, l in RL]
res_rows.insert(0, {"k": "ne", "label": "Natural Earth 10m", "n": len(nea), "ge01": sum(a >= .1 for a in nea), "ge1": sum(a >= 1 for a in nea),
                    "ge10": sum(a >= 10 for a in nea), "ge100": sum(a >= 100 for a in nea), "ge1000": sum(a >= 1000 for a in nea), "min_km2": min(nea),
                    "n_land": len(NEc["ne_10m_land"]), "n_minor": len(NEc["ne_10m_minor_islands"])})
R["res"] = res_rows
R["res_ratio_fc"] = RES["f"]["n_all"] / RES["c"]["n_all"]
R["res_ratio_fne"] = RES["f"]["n_all"] / len(nea)

# ---------- regions ----------
reg = []
for k, l in REGIONS:
    sel = [o for o in I if o["r"] == k]
    big = max(sel, key=lambda o: o["area"]); mp = max(sel, key=lambda o: o["pop"])
    reg.append({"k": k, "name": l, "n": len(sel), "ge1": sum(o["area"] >= 1 for o in sel), "ge10": sum(o["area"] >= 10 for o in sel),
                "area": sum(o["area"] for o in sel), "pop": sum(o["pop"] for o in sel), "pct_pop": pc(sum(o["pop"] for o in sel), ISL_POP),
                "largest": brief(big), "most_pop": brief(mp)})
R["regions"] = reg

# ---------- countries ----------
cc = defaultdict(list)
for o in I:
    cc[o["c"]].append(o)
crow = []
for c, sel in cc.items():
    tp = CPOP.get(c, [0, 0])
    big = max(sel, key=lambda o: o["area"]); mp = max(sel, key=lambda o: o["pop"])
    crow.append({"c": c, "name": CN.get(c, c), "sov": sel[0]["sov"], "n": len(sel), "ge1": sum(o["area"] >= 1 for o in sel),
                 "ge10": sum(o["area"] >= 10 for o in sel), "ge100": sum(o["area"] >= 100 for o in sel), "area": sum(o["area"] for o in sel),
                 "isl_pop": sum(o["pop"] for o in sel), "people": tp[0], "people_isl": tp[1], "pct_isl": pc(tp[1], tp[0]),
                 "largest": brief(big), "most_pop": brief(mp), "r": max(Counter(o["r"] for o in sel).items(), key=lambda t: t[1])[0],
                 "bbox": [round(min(o["lon"] for o in sel), 2), round(min(o["lat"] for o in sel), 2), round(max(o["lon"] for o in sel), 2), round(max(o["lat"] for o in sel), 2)]})
for c, tp in CPOP.items():          # countries with people but no island
    if c not in cc and tp[0] > 0:
        crow.append({"c": c, "name": CN.get(c, c), "sov": c, "n": 0, "ge1": 0, "ge10": 0, "ge100": 0, "area": 0, "isl_pop": 0, "people": tp[0],
                     "people_isl": tp[1], "pct_isl": pc(tp[1], tp[0]), "largest": None, "most_pop": None, "r": None, "bbox": None})
crow.sort(key=lambda d: -d["n"])
R["countries_n"] = len([d for d in crow if d["n"]])
top_all = sorted([d for d in crow if d["n"]], key=lambda d: -d["n"])
top_ge1 = sorted([d for d in crow if d["n"]], key=lambda d: -d["ge1"])
top_ge10 = sorted([d for d in crow if d["n"]], key=lambda d: -d["ge10"])
strip = lambda d: {k: v for k, v in d.items() if k not in ("largest", "most_pop", "bbox")}
R["top_countries"] = {"all": [strip(d) for d in top_all[:20]], "ge1": [strip(d) for d in top_ge1[:20]], "ge10": [strip(d) for d in top_ge10[:20]]}
# sovereign states (territories folded in: Greenland and the Faroes with Denmark, and so on)
sv = defaultdict(lambda: [0, 0, 0])
for o in I:
    sv[o["sov"]][0] += 1; sv[o["sov"]][1] += o["area"] >= 1; sv[o["sov"]][2] += o["area"] >= 10
R["top_sov"] = [{"sov": s, "name": SOVN.get(s, s), "n": v[0], "ge1": v[1], "ge10": v[2]} for s, v in sorted(sv.items(), key=lambda kv: -kv[1][0])[:10]]
# people: island nations and mixed countries
withp = [d for d in crow if d["people"] >= 1e5]
R["island_nations"] = {"n99": sum(1 for d in crow if d["people"] > 0 and d["pct_isl"] >= 99), "n99_100k": sum(1 for d in withp if d["pct_isl"] >= 99),
                       "people99": sum(d["people"] for d in crow if d["people"] > 0 and d["pct_isl"] >= 99),
                       "mixed": sorted([{"c": d["c"], "name": d["name"], "pct": d["pct_isl"], "people_isl": d["people_isl"], "people": d["people"]}
                                        for d in crow if d["people"] >= 1e6 and 5 <= d["pct_isl"] < 95], key=lambda d: -d["pct"])}

# ---------- population ----------
top_pop = [brief(o, ("dens", "rank_area", "rank_pop")) for o in popd[:40]]
R["pop"] = {"world": WORLD_POP, "isl": ISL_POP, "pct": pc(ISL_POP, WORLD_POP), "cont": {CONTINENT_IDS[c]: POP.get(str(next(k for k, p in enumerate(POLY) if p["id"] == c)), 0) for c in CONTINENT_IDS},
            "unplaced": PST["unplaced"], "touch": PST["touch"], "near": PST["near"],
            "top": top_pop, "top3": sum(o["pop"] for o in popd[:3]), "top3_pct_isl": pc(sum(o["pop"] for o in popd[:3]), ISL_POP),
            "top10_pct_isl": pc(sum(o["pop"] for o in popd[:10]), ISL_POP), "top3_pct_world": pc(sum(o["pop"] for o in popd[:3]), WORLD_POP),
            "java_pct_world": pc(popd[0]["pop"], WORLD_POP), "java_pct_isl": pc(popd[0]["pop"], ISL_POP),
            "n_inhabited": sum(1 for o in I if o["pop"] >= 1), "n_100": sum(1 for o in I if o["pop"] >= 100), "n_1m": sum(1 for o in I if o["pop"] >= 1e6),
            "n_100k": sum(1 for o in I if o["pop"] >= 1e5), "ge1_inhabited_pct": pc(sum(1 for o in I if o["pop"] >= 1 and o["area"] >= 1), ge(1)),
            "lake_pop": sum(o["pop"] for o in I if o["kind"] == "lakeisl"),
            "n_places_isl": sum(1 for o in I if o.get("place"))}
# density: most crowded islands, by size band; emptiest big islands
dens = {}
for k, lo in (("ge1", 1), ("ge100", 100), ("ge1000", 1000)):
    dens[k] = [brief(o, ("dens",)) for o in sorted([o for o in I if o["area"] >= lo and o["pop"] > 0], key=lambda o: -o["dens"])[:12]]
R["dens"] = dens
R["dens_java"] = popd[0]["dens"]
R["empty"] = [brief(o) for o in I if o["pop"] < 0.5 and o["kind"] != "ant"][:12]
R["empty_n_ge1000"] = sum(1 for o in I if o["pop"] < 0.5 and o["area"] >= 1000 and o["kind"] != "ant")
R["empty_area_pct"] = pc(sum(o["area"] for o in I if o["pop"] < 0.5 and o["kind"] != "lakeisl"), isl_area)
R["largest"] = [brief(o, ("rank_pop", "dens", "shares")) for o in I[:30]]
R["largest_lake"] = [brief(o, ("lake", "lake_km2", "river")) for o in I if o["kind"] == "lakeisl"][:10]
R["largest_ant"] = [brief(o) for o in I if o["kind"] == "ant"][:5]
R["shared"] = [brief(o, ("shares",)) for o in I if len(o.get("shares") or []) > 1]

# ---------- islands in lakes on islands ----------
isl_ids = {o["id"] for o in I if o["kind"] in ("sea", "ant")}
iby = {o["id"]: o for o in I}
lakes_on = [p for p in POLY if p["kind"] == "lake" and p.get("parent") in isl_ids]
lakes_on.sort(key=lambda p: -abs(p["area"]))
nest = sorted([o for o in I if o["kind"] == "lakeisl" and o.get("lake_on") in isl_ids], key=lambda o: -o["area"])
R["nest"] = {"lakes_on_isl": len(lakes_on), "lakes_on_isl_pct": pc(len(lakes_on), R["counts"]["lakes"]),
             "biggest_lake": {"id": lakes_on[0]["id"], "km2": abs(lakes_on[0]["area"]), "on": lakes_on[0]["parent"], "on_name": iby[lakes_on[0]["parent"]]["name"],
                              "lon": lakes_on[0]["lon"], "lat": lakes_on[0]["lat"]},
             "n": len(nest), "top": [dict(brief(o), lake_km2=o["lake_km2"], on=o["lake_on"], on_name=iby[o["lake_on"]]["name"], on_km2=iby[o["lake_on"]]["area"]) for o in nest[:8]]}
R["meta"]["swe_official"] = 267570      # Statistics Sweden (SCB), 2013, from the national property map: quoted for comparison
cpct = {d["c"]: d for d in crow}
for c in ("DNK", "HKG", "MYS", "GRC", "CAN", "ITA"):
    R[c.lower()] = {"pct": cpct[c]["pct_isl"], "people_isl": cpct[c]["people_isl"],
                    "top": [o["name"] for o in sorted([o for o in I if o["c"] == c], key=lambda o: -o["pop"])[:3]]}
R["swe"] = {"n": cpct["SWE"]["n"], "ge1": cpct["SWE"]["ge1"]}
R["fin_lake_pct"] = pc(sum(1 for o in I if o["c"] == "FIN" and o["kind"] == "lakeisl"), cpct["FIN"]["n"])
R["java_one_in"] = WORLD_POP / popd[0]["pop"]
R["aus_greenland"] = byid["6"]["area"] / I[0]["area"]
R["res_spread"] = max(RES[k]["ge"]["1"] for k in ("i", "h", "f")) - min(RES[k]["ge"]["1"] for k in ("i", "h", "f"))
R["classes_sub1_pct"] = cls_rows[0]["pct_n"] + cls_rows[1]["pct_n"]
R["classes_ge10k_pop"] = cls_rows[6]["pct_pop"] + cls_rows[7]["pct_pop"]
R["empty_polar_n"] = sum(1 for o in I if o["pop"] < 0.5 and o["area"] >= 1000 and o["kind"] != "ant" and (o["lat"] > 60 or o["lat"] < -45))
R["baltic_n"] = sum(1 for o in I if 17.6 <= o["lon"] <= 23.4 and 59.05 <= o["lat"] <= 60.75)     # Stockholm to Turku close-up
R["baltic_ge1"] = sum(1 for o in I if 17.6 <= o["lon"] <= 23.4 and 59.05 <= o["lat"] <= 60.75 and o["area"] >= 1)
jsave(R, f"{DATA}/results.json", indent=1)

# ---------- data files ----------
with gzip.open(f"{DATA}/islands.csv.gz", "wt", newline="", encoding="utf-8", compresslevel=9) as f:
    w = csv.writer(f)
    w.writerow(["gshhg_id", "kind", "area_km2", "size_class", "lon", "lat", "country", "country_name", "sovereign", "region", "name",
                "largest_place", "population_2025", "people_per_km2", "rank_area", "rank_population", "lake_gshhg_id", "lake_km2", "country_shares"])
    for o in I:
        w.writerow([o["id"], {"sea": "sea island", "lakeisl": "island in a lake or river", "ant": "Antarctic island"}[o["kind"]],
                    f"{o['area']:.4f}" if o["area"] < 10 else f"{o['area']:.1f}", CLASSES[o["cls"]][1], f"{o['lon']:.4f}", f"{o['lat']:.4f}", o["c"],
                    CN.get(o["c"], o["c"]), SOVN.get(o["sov"], o["sov"]), RN[o["r"]], dash(o["name"] or ""), o.get("place") or "",
                    rnd(o["pop"]), f"{o['dens']:.1f}", o["rank_area"], o.get("rank_pop", ""), o.get("lake", ""),
                    f"{o['lake_km2']:.1f}" if o.get("lake_km2") else "", ";".join(f"{a}:{b}" for a, b in o.get("shares") or [] if len(o["shares"]) > 1)])
with open(f"{DATA}/countries.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["country", "name", "islands", "islands_ge_1km2", "islands_ge_10km2", "islands_ge_100km2", "island_area_km2",
                "people_2025", "people_on_islands", "pct_on_islands", "largest_island", "most_populous_island"])
    for d in sorted(crow, key=lambda d: (-d["n"], -d["people"])):
        w.writerow([d["c"], d["name"], d["n"], d["ge1"], d["ge10"], d["ge100"], round(d["area"], 1), rnd(d["people"]), rnd(d["people_isl"]),
                    "" if d["pct_isl"] is None else round(d["pct_isl"], 2), d["largest"]["name"] if d["largest"] else "", d["most_pop"]["name"] if d["most_pop"] else ""])
with open(f"{DATA}/regions.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["region", "islands", "islands_ge_1km2", "islands_ge_10km2", "island_area_km2", "people_on_islands"])
    for d in reg:
        w.writerow([d["name"], d["n"], d["ge1"], d["ge10"], round(d["area"]), rnd(d["pop"])])
with open(f"{DATA}/size_classes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["size_class", "islands", "area_km2", "people", "inhabited_islands"])
    for d in cls_rows:
        w.writerow([d["label"], d["n"], round(d["area"], 1), rnd(d["pop"]), d["inhabited"]])
with open(f"{DATA}/resolutions.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["map", "islands", "ge_0.1km2", "ge_1km2", "ge_10km2", "ge_100km2", "ge_1000km2", "smallest_km2"])
    for d in res_rows:
        w.writerow([d["label"], d["n"], d["ge01"], d["ge1"], d["ge10"], d["ge100"], d["ge1000"], round(d["min_km2"], 6)])
jsave({"islands": I, "countries": crow, "cname": CN}, f"{WORK}/isl_final.json")

# ---------- summary ----------
c = R["counts"]
print("islands", N, "ge1", c["ge1"], "ge10", c["ge10"], "ge1000", c["ge1000"], "isl area %", round(c["isl_area_pct"], 2))
print("pop on islands", round(ISL_POP / 1e6, 1), "M", round(R["pop"]["pct"], 2), "%")
print("top countries all", [(d["c"], d["n"]) for d in top_all[:8]])
print("top countries ge1", [(d["c"], d["ge1"]) for d in top_ge1[:8]])
print("top countries ge10", [(d["c"], d["ge10"]) for d in top_ge10[:8]])
print("sov", [(d["sov"], d["n"]) for d in R["top_sov"][:6]])
print("dens ge100", [(d["name"], d["c"], round(d["area"]), rnd(d["pop"] / d["area"])) for d in dens["ge100"][:8]])
print("dens ge1", [(d["name"], d["c"], d["place"], round(d["area"], 2), rnd(d["pop"] / d["area"])) for d in dens["ge1"][:8]])
print("dens ge1000", [(d["name"], d["c"], round(d["area"]), rnd(d["pop"] / d["area"])) for d in dens["ge1000"][:8]])
print("empty", [(d["name"], d["c"], round(d["area"])) for d in R["empty"][:8]], R["empty_n_ge1000"])
print("nest", R["nest"]["n"], R["nest"]["biggest_lake"], [(d["id"], round(d["area"], 1), d["on_name"], round(d["lake_km2"])) for d in R["nest"]["top"][:5]])
print("lake isl", [(d["name"], round(d["area"]), d["river"]) for d in R["largest_lake"][:6]])
print("regions", [(d["k"], d["n"], d["ge1"], rnd(d["pop"] / 1e6)) for d in reg])
print("res", [(d["k"], d["n"], d["ge1"]) for d in res_rows])
print("island nations", R["island_nations"]["n99"], R["island_nations"]["n99_100k"], rnd(R["island_nations"]["people99"] / 1e6))
print("unnamed in top pop", [(d["id"], d["c"], d["place"], rnd(d["pop"])) for d in top_pop if not d["name"]])
