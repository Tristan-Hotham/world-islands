"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23848301, https://doi.org/10.5281/zenodo.23848301 and https://blog.tristanhotham.com/2026/10/31/world-islands/ stay as placeholders for the publisher."""
import re, zipfile, json as _json, importlib.util
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "07_build_site.py"))
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)          # shared fact checks
R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release")
NAME = "Hotham_World_Islands"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}

# facts stated in words in the blog (alt text included)
K = R["classes"]
assert K[0]["n"] == 93998 and K[7]["n"] == 18 and rnd(K[7]["pct_area"]) == 70 and rnd(K[7]["pct_pop"]) == 65
assert [d["n"] for d in R["res"]] == [9628, 762, 6242, 34392, 146510, 181588] and all(22500 < d["ge1"] < 23500 for d in R["res"][3:])
assert R["counts"]["min_m2"] < 261                                             # smaller than a tennis court
T = R["pop"]["top"]
assert [rnd(d["pop"] / 1e6) for d in T[:5]] == [153, 100, 67, 61, 57] and T[19]["name"] == "Hokkaido" and rnd(T[19]["pop"] / 1e6) == 5
D = R["dens"]["ge100"]
assert [d["name"] for d in D[4:8]] == ["Batam", "Penang Island", "Long Island", "Phuket"]
assert round(D[0]["dens"], -2) == 18800 and round(D[1]["dens"], -2) == 10700
assert [d["name"] for d in R["empty"][:4]] == ["Devon Island", "Melville", "Axel Heiberg", "Spitsbergen"] and R["empty"][0]["area"] > 55000
lk = {d["name"]: d["pop"] for d in R["largest_lake"]}
assert lk["Montreal and Laval (joined in GSHHG)"] > R["can"]["people_isl"] / 2                 # Canada: mostly Montreal
assert R["dnk"]["top"][:2] == ["Zealand", "Funen"]

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = B.fill(post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
for ln in post.splitlines():                       # image tokens stand alone on their own lines
    if "{{IMG|" in ln:
        assert ln.startswith("{{IMG|") and ln.endswith("}}"), ln
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Where the world's islands are",
        "slug": SLUG,
        "excerpt": f"I counted every island in a detailed open map of the world's shorelines: {R['counts']['n']:,} of them, {R['counts']['ge1']:,} over a square kilometre. Canada has the most, and {R['pop']['pct']:.1f}% of the world's people live on one.",
        "seo_description": f"Every island in the world mapped: {R['counts']['n']:,} in the GSHHG shoreline, who has them, and the {rnd(R['pop']['isl'] / 1e6)} million people who live on them.",
        "tags": ["islands", "geography", "population", "maps", "data visualisation", "GSHHG", "WorldPop", "coastlines"],
        "header_alt": f"Title card reading 'Where the world's islands are' in dark slate and indigo on pale paper, beside a world map where every island is coloured by size, deep indigo for Greenland, Britain, Japan and Indonesia and gold threads of tiny islands along the coasts, with the text '{R['counts']['n']:,} islands' and '{R['pop']['pct']:.1f}% of people live on one'."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)


def link(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    os.link(src, dst)


link(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__" or fn in ("points.json", "outlines.geojson", "tiles.json", "world.json", "cities.json", "site.json"):
                continue                     # page-only files, rebuilt by the code
            z.write(os.path.join(ROOT, d, fn), f"{SLUG}/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        if os.path.exists(os.path.join(ROOT, fn)):
            z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("km$^2$", "km²").replace("\\emph{", "").replace("}", "").replace("\\&", "&")
assert "\\" not in ab and "$" not in ab, ab
zmeta = {"title": "Where the World's Islands Are: Counting, Measuring and Peopling Every Island in the GSHHG Shoreline",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: {PAGE}. Data and code: {REPO}. Blog post: {{https://blog.tristanhotham.com/2026/10/31/world-islands/}}.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["islands", "shorelines", "GSHHG", "WorldPop", "population", "coastline paradox", "Natural Earth", "geography", "maps"],
         "license": "cc-by-4.0",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.soest.hawaii.edu/pwessel/gshhg/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.worldpop.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}]}
jsave(zmeta, f"{Z}/metadata.json", indent=2)
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in s and "\u2013" not in s and "--" not in s
print("blog words", words, "; zenodo files", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
