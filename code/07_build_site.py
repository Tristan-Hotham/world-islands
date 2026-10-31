"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; results and site data are embedded; points, outlines, borders, place names and the island tiles are
loaded by the page. Facts stated in words are checked here (and reused by the blog, paper and collage).
10.5281/zenodo.23848301, https://doi.org/10.5281/zenodo.23848301 and https://blog.tristanhotham.com/2026/10/31/world-islands/ stay as placeholders for the publisher. The full-screen snippet is pasted before </body>."""
import re
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
KEEP = {"DOI", "BLOG_URL", "DOI_URL"}


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{rnd(v):,}"
    if f == "pc": return f"{rnd(v)}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "m0": return f"{rnd(v / 1e6):,}"
    if f == "m1": return f"{v / 1e6:,.1f}"
    raise ValueError(f)


def fill(tpl, fm=fmt):
    return re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fm(get(m.group(1)), m.group(3)), tpl)


def check():
    """Facts stated in words on the page, blog, paper and collage."""
    T = R["top_countries"]
    assert T["all"][0]["c"] == T["ge1"][0]["c"] == T["ge10"][0]["c"] == "CAN"
    assert [d["c"] for d in T["all"][1:6]] == ["GRL", "FIN", "USA", "NOR", "SWE"], [d["c"] for d in T["all"][:7]]
    assert [d["c"] for d in T["ge1"][1:5]] == ["USA", "IDN", "RUS", "CHL"]
    assert R["fin_lake_pct"] < 2                                         # Finland's GSHHG islands are nearly all at sea
    L = [d["name"] for d in R["largest"]]
    assert L[:6] == ["Greenland", "New Guinea", "Borneo", "Madagascar", "Baffin", "Sumatra"], L[:8]
    assert R["counts"]["ge100000"] == 18 and L[17] == "Iceland"
    sh = {d["name"] for d in R["shared"]}
    assert {"New Guinea", "Borneo", "Ireland", "Hispaniola", "Timor", "Tierra del Fuego", "Cyprus"} <= sh, sh
    assert 3 < R["aus_greenland"] < 4                                      # 'more than three times Greenland'
    P = [d["name"] for d in R["pop"]["top"]]
    assert P[:11] == ["Java", "Honshu", "Great Britain", "Luzon", "Sumatra", "Madagascar", "Mindanao", "Borneo", "Hispaniola", "Sri Lanka", "Taiwan"], P[:12]
    rg = {d["k"]: d for d in R["regions"]}
    assert R["pop"]["top"][0]["pop"] > rg["eur"]["pop"]                      # Java holds more people than all Europe's islands
    assert R["dnk"]["top"][:2] == ["Zealand", "Funen"] and R["ita"]["top"][:2] == ["Sicily", "Sardinia"]
    assert R["can"]["top"][:3] == ["Montreal and Laval (joined in GSHHG)", "Vancouver Island", "Newfoundland"], R["can"]["top"]
    assert R["mys"]["top"][0] == "Penang Island"
    mx = [d["c"] for d in R["island_nations"]["mixed"]]
    assert mx[:6] == ["DNK", "GNQ", "HKG", "MYS", "GRC", "CAN"] and mx[6] == "ITA", mx
    d = [x["name"] for x in R["dens"]["ge100"]]
    assert d[:4] == ["Xiamen Island", "Singapore", "Montreal and Laval (joined in GSHHG)", "Staten Island"], d[:5]
    assert [x["name"] for x in R["dens"]["ge1000"][:2]] == ["Long Island", "Java"]
    e = [x["name"] for x in R["empty"]]
    assert e[0] == "Devon Island" and "Spitsbergen" in e[:5]
    nt = [x["id"] for x in R["nest"]["top"][:4]]
    assert nt == ["187208", "187466", "187481", "187509"] and R["nest"]["top"][0]["name"] == "Glover Island"
    assert R["nest"]["biggest_lake"]["id"] == "180553" and R["nest"]["biggest_lake"]["on_name"] == "Baffin"     # Amadjuak Lake
    assert R["counts"]["under01_pct"] > 50 and R["classes"][0]["pct_area"] < .1   # 'less than a tenth of one per cent'
    assert R["res"][3]["ge1"] < R["res"][4]["ge1"] < R["res"][5]["ge1"] and R["res"][5]["ge1"] - R["res"][3]["ge1"] < 500


check()


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl)
    left = set(re.findall(r"\{\{([^}]+)\}\}", html))
    assert left <= KEEP, left
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    Rp = {k: R[k] for k in ("counts", "classes", "res", "regions", "top_countries", "pop", "dens", "empty", "largest", "nest")}
    html = html.replace("/*RESULTS*/", J(Rp)).replace("/*SITE*/", J(SITE)).replace("/*TILES*/", open(f"{DATA}/tiles.json").read())
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
