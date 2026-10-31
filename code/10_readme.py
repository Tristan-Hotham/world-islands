"""README.md, LICENSE and reddit/post.md, numbers from data/results.json."""
import gzip
from common import *

R = jload(f"{DATA}/results.json")
C, P, T = R["counts"], R["pop"], R["top_countries"]
size_raw = lambda: f"{len(gzip.open(os.path.join(DATA, 'islands.csv.gz')).read()) / 1e6:.1f} MB"
size = lambda fn: f"{os.path.getsize(os.path.join(DATA, fn)) / 1e6:.1f} MB"
m = lambda v: f"{v / 1e6:,.1f}"
readme = f"""# Where the world's islands are

Count, size and people: every island in the full-resolution GSHHG world shoreline ({C['n']:,} of them), with its area, country, rank and the number of people living on it in 2025 from WorldPop. With the island count at every GSHHG resolution and in Natural Earth, to show how much the number depends on the map.

Interactive page: {PAGE}
Paper: https://doi.org/{{10.5281/zenodo.23848301}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/world-islands/}}

## Headline results

- GSHHG at full resolution draws {C['n']:,} islands: {C['sea']:,} at sea, {C['lake']:,} in lakes and rivers and {C['ant']} around Antarctica. {C['under01_pct']:.1f}% are under 0.1 km²; {C['ge1']:,} are 1 km² or more, {C['ge10']:,} are 10 km² or more, {C['ge1000']} are 1,000 km² or more and {C['ge100000']} are over 100,000 km².
- The count depends on the map: from {R['res'][1]['n']:,} islands (GSHHG crude) to {R['res'][5]['n']:,} (full); Natural Earth 10m has {R['res'][0]['n']:,}. Islands of 1 km² or more agree within {R['res_spread']} across the three finest GSHHG versions ({R['res'][3]['ge1']:,} to {R['res'][5]['ge1']:,}).
- Canada has the most islands on every threshold: {T['all'][0]['n']:,} in all and {T['ge1'][0]['ge1']:,} of 1 km² or more. At 1 km² or more the United States ({T['ge1'][1]['ge1']:,}), Indonesia ({T['ge1'][2]['ge1']:,}), Russia ({T['ge1'][3]['ge1']:,}) and Chile ({T['ge1'][4]['ge1']:,}) follow.
- Islands cover {C['isl_area_pct']:.1f}% of the world's land; Greenland alone is {C['greenland_pct_isl_area']:.1f}% of island land.
- {m(P['isl'])} million people, {P['pct']:.1f}% of the {m(P['world'])} million in WorldPop's 2025 grid, live on islands. Java ({m(P['top'][0]['pop'])} million), Honshu ({m(P['top'][1]['pop'])} million) and Great Britain ({m(P['top'][2]['pop'])} million) hold {P['top3_pct_isl']:.1f}% of them.
- Most crowded island of 100 km² or more: Xiamen Island ({rnd(R['dens']['ge100'][0]['dens']):,} people per km²), then Singapore. Largest island with no one in the grid: Devon Island ({rnd(R['empty'][0]['area']):,} km²). Largest island in a lake on an island: Glover Island, Newfoundland ({rnd(R['nest']['top'][0]['area'])} km²).
- Caveats: counts under 1 km² depend on resolution; GSHHG joins Manhattan, Salsette and Samosir to their neighbours, joins Montreal and Laval, splits the Brodeur Peninsula from Baffin Island and lacks Nettilling Lake and most islands in Finland's lakes; WorldPop is a model and misses some small settlements (Longyearbyen).

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`; results embedded; `data/points.json`, `data/outlines.geojson`, `data/world.json`, `data/cities.json` and `tiles/` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/islands.csv.gz` | All {C['n']:,} islands (gzipped CSV): GSHHG id, kind, area, size class, point, country, sovereign, region, name, largest Natural Earth place, people in 2025, people per km², rank by area and by people, lake, country shares of big shared islands ({size('islands.csv.gz')}; {size_raw()} unpacked). |
| `data/countries.csv` | Islands by country or territory (all, 1, 10, 100 km² or more), island area, people and people on islands, largest and most populous island. |
| `data/regions.csv`, `data/size_classes.csv`, `data/resolutions.csv` | Islands by region, by size class, and by map and resolution. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/points.json`, `data/outlines.geojson`, `data/tiles.json`, `tiles/` | Page data: every island as a point, outlines of the {C['ge100']:,} islands of 100 km² or more (simplified), and raster tiles of all islands by size (zoom 1 to 6). Derived from GSHHG (LGPL-3.0). |
| `data/world.json`, `data/cities.json`, `data/site.json` | Natural Earth borders and place names, country summaries for the page. |
| `code/` | Scripts, run in order (below), the page, paper and blog templates, `names.py` (hand-assigned island names) and `qa.js`. |
| `release/` | Paper PDF and LaTeX source with figures, blog post and figures, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Islands: GSHHG 2.3 full resolution. Every level-1 polygon except the five continents (over 5 million km²) is a sea island, every level-3 polygon an island in a lake or river, and Antarctic level-5 polygons other than the continent are Antarctic islands. Pieces cut at the date line are joined. Area is GSHHG's own, within the coastline.
- Countries: the Natural Earth 10m country under each island, else the nearest; islands over 1,000 km² go to the country with the largest share, measured geodesically. Regions from Natural Earth continents, with a few geographic exceptions (listed in `code/02_countries.py`). Names from Natural Earth physical labels, plus hand-assigned names for larger islands (`code/names.py`).
- People: WorldPop Global 2 (R2024B) constrained 2025 estimate at 30 arc seconds, as re-tiled by github.com/nn0000asdf/world-population-3d. Each cell goes to the polygon under its centre, else a polygon touching it, else the nearest land within two cells; {m(P['unplaced'])} million people could not be placed. Country totals use Natural Earth 10m.
- Resolutions: island counts at the four coarser GSHHG resolutions from their meta files, and Natural Earth 10m land and minor islands.

## How to rerun

Needs Python 3 with numpy, shapely (2.x), pyproj, rasterio, scipy, matplotlib, Pillow and fontTools, xelatex (TeX Gyre Pagella, Inter) and pdftotext, and node with Playwright for the QA screenshots. Raw inputs (paths in `code/common.py`, or set `WI_COAST`, `WI_GEO`, `WI_RAW`):

- GSHHG: `pip download basemap-data basemap-data-hires` (2.0.0) and unpack `mpl_toolkits/basemap_data/gshhs_*.dat` and `gshhsmeta_*.dat`.
- WorldPop tiles: `docs/tiles/L3/` (957 files and `_meta.json`) from https://github.com/nn0000asdf/world-population-3d, retrieved in {RETRIEVED}.
- Natural Earth 10m (from https://github.com/nvkelso/natural-earth-vector): admin-0 countries, geography regions polygons and points, land, minor islands, populated places; 50m countries.

Intermediate files go to `/dev/shm/wi/work` (`WITMP`).

```
python3 code/01_gshhg.py        # read GSHHG, build the island list, counts at every resolution
python3 code/02_countries.py    # country, region and name for every island (slow: about 8 minutes)
python3 code/03_population.py   # WorldPop people per island and per country
python3 code/04_results.py      # results.json and data tables
python3 code/05_mapdata.py      # tiles, points, outlines and page data (WI_TILES=1 to redraw tiles)
python3 code/06_figures.py      # header, blog and paper figures
python3 code/07_build_site.py   # index.html (and the shared fact checks)
python3 code/08_paper.py        # paper PDF
python3 code/10_readme.py       # README, LICENSE, Reddit post
python3 code/09_release.py      # blog post, Zenodo files
python3 reddit/collage.py       # collage
```

## Sources and licences

- GSHHG 2.3, Global Self-consistent, Hierarchical, High-resolution Geography database (Wessel, P. and Smith, W. H. F.), via the basemap-data and basemap-data-hires Python packages. LGPL-3.0. The island tiles, outlines and points in this repository are derived from it and are LGPL-3.0.
- WorldPop Global 2, R2024B, constrained population 2025, 30 arc seconds (WorldPop, University of Southampton, https://www.worldpop.org/). CC BY 4.0. Re-tiled by https://github.com/nn0000asdf/world-population-3d (MIT). Only aggregates per island and per country are published here.
- Natural Earth (public domain).
- Sweden's official count of {R['meta']['swe_official']:,} islands: Statistics Sweden (2013), quoted for comparison.
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Where the world's islands are: counting, measuring and peopling every island in the GSHHG shoreline. Zenodo. https://doi.org/{{10.5281/zenodo.23848301}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and derived tables (data/*.csv, data/results.json): Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/

Exceptions:
- Island outlines, points and raster tiles derived from GSHHG (data/outlines.geojson, data/points.json, tiles/) are distributed under the GNU Lesser General Public License v3.0, as GSHHG is: https://www.gnu.org/licenses/lgpl-3.0.html
- Population figures derive from WorldPop (CC BY 4.0); credit WorldPop, University of Southampton.
- Natural Earth data is in the public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
post = f"""# Reddit post (r/dataisbeautiful)

**Title:** [OC] A detailed open map of the world's shorelines has {C['n']:,} islands, and {m(P['isl']).split('.')[0]} million people ({P['pct']:.1f}% of humanity) live on one

**Image:** reddit/world_islands.png

**Body:**

I counted every island in GSHHG, the free full-resolution world shoreline used inside a lot of mapping software, and gave each one a size, a country and a population (WorldPop, 2025).

- {C['n']:,} islands, but {C['under01_pct']:.0f}% are under 0.1 km². {C['ge1']:,} are 1 km² or more.
- The total depends on the map: the crude version of the same shoreline has {R['res'][1]['n']:,} islands, Natural Earth 10m has {R['res'][0]['n']:,}. Islands over 1 km² barely change between the finer versions.
- Canada has the most at every threshold ({T['ge1'][0]['ge1']:,} of 1 km² or more).
- Java alone has {m(P['top'][0]['pop'])} million people, more than all of Europe's islands combined, Great Britain included.
- Largest island in a lake on an island: Glover Island, Newfoundland ({rnd(R['nest']['top'][0]['area'])} km²).

Interactive map (search any country, click any island): {PAGE}

**Source comment:**

Data: GSHHG 2.3 full-resolution shorelines (Wessel and Smith, LGPL-3.0); WorldPop Global 2, 2025 constrained estimate at about 1 km (CC BY 4.0), via the world-population-3d tiles on GitHub; Natural Earth (public domain). Tools: Python (shapely, rasterio, matplotlib). Islands are all land except the five continents, plus islands in lakes and around Antarctica. Caveats: counts under 1 km² depend on resolution; the shoreline joins Manhattan and Mumbai's Salsette Island to the mainland; WorldPop is a model and misses some tiny settlements. Paper, data and code: {REPO}
"""
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
for t in (readme, lic, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in t.replace("|---|---|", ""), bad
print("readme, licence, post written")
