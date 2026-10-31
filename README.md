# Where the world's islands are

Count, size and people: every island in the full-resolution GSHHG world shoreline (181,588 of them), with its area, country, rank and the number of people living on it in 2025 from WorldPop. With the island count at every GSHHG resolution and in Natural Earth, to show how much the number depends on the map.

Interactive page: https://maps.tristanhotham.com/world-islands/
Paper: https://doi.org/{10.5281/zenodo.23848301}
Blog post: {https://blog.tristanhotham.com/2026/10/31/world-islands/}

## Headline results

- GSHHG at full resolution draws 181,588 islands: 179,823 at sea, 1,437 in lakes and rivers and 328 around Antarctica. 51.8% are under 0.1 km²; 23,150 are 1 km² or more, 6,341 are 10 km² or more, 296 are 1,000 km² or more and 18 are over 100,000 km².
- The count depends on the map: from 762 islands (GSHHG crude) to 181,588 (full); Natural Earth 10m has 9,628. Islands of 1 km² or more agree within 378 across the three finest GSHHG versions (22,772 to 23,150).
- Canada has the most islands on every threshold: 29,249 in all and 4,048 of 1 km² or more. At 1 km² or more the United States (1,652), Indonesia (1,544), Russia (1,438) and Chile (1,245) follow.
- Islands cover 6.6% of the world's land; Greenland alone is 21.4% of island land.
- 841.3 million people, 10.3% of the 8,187.6 million in WorldPop's 2025 grid, live on islands. Java (153.2 million), Honshu (100.4 million) and Great Britain (66.8 million) hold 38.1% of them.
- Most crowded island of 100 km² or more: Xiamen Island (18,787 people per km²), then Singapore. Largest island with no one in the grid: Devon Island (55,886 km²). Largest island in a lake on an island: Glover Island, Newfoundland (163 km²).
- Caveats: counts under 1 km² depend on resolution; GSHHG joins Manhattan, Salsette and Samosir to their neighbours, joins Montreal and Laval, splits the Brodeur Peninsula from Baffin Island and lacks Nettilling Lake and most islands in Finland's lakes; WorldPop is a model and misses some small settlements (Longyearbyen).

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`; results embedded; `data/points.json`, `data/outlines.geojson`, `data/world.json`, `data/cities.json` and `tiles/` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/islands.csv.gz` | All 181,588 islands (gzipped CSV): GSHHG id, kind, area, size class, point, country, sovereign, region, name, largest Natural Earth place, people in 2025, people per km², rank by area and by people, lake, country shares of big shared islands (3.5 MB; 19.8 MB unpacked). |
| `data/countries.csv` | Islands by country or territory (all, 1, 10, 100 km² or more), island area, people and people on islands, largest and most populous island. |
| `data/regions.csv`, `data/size_classes.csv`, `data/resolutions.csv` | Islands by region, by size class, and by map and resolution. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/points.json`, `data/outlines.geojson`, `data/tiles.json`, `tiles/` | Page data: every island as a point, outlines of the 1,512 islands of 100 km² or more (simplified), and raster tiles of all islands by size (zoom 1 to 6). Derived from GSHHG (LGPL-3.0). |
| `data/world.json`, `data/cities.json`, `data/site.json` | Natural Earth borders and place names, country summaries for the page. |
| `code/` | Scripts, run in order (below), the page, paper and blog templates, `names.py` (hand-assigned island names) and `qa.js`. |
| `release/` | Paper PDF and LaTeX source with figures, blog post and figures, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Islands: GSHHG 2.3 full resolution. Every level-1 polygon except the five continents (over 5 million km²) is a sea island, every level-3 polygon an island in a lake or river, and Antarctic level-5 polygons other than the continent are Antarctic islands. Pieces cut at the date line are joined. Area is GSHHG's own, within the coastline.
- Countries: the Natural Earth 10m country under each island, else the nearest; islands over 1,000 km² go to the country with the largest share, measured geodesically. Regions from Natural Earth continents, with a few geographic exceptions (listed in `code/02_countries.py`). Names from Natural Earth physical labels, plus hand-assigned names for larger islands (`code/names.py`).
- People: WorldPop Global 2 (R2024B) constrained 2025 estimate at 30 arc seconds, as re-tiled by github.com/nn0000asdf/world-population-3d. Each cell goes to the polygon under its centre, else a polygon touching it, else the nearest land within two cells; 1.5 million people could not be placed. Country totals use Natural Earth 10m.
- Resolutions: island counts at the four coarser GSHHG resolutions from their meta files, and Natural Earth 10m land and minor islands.

## How to rerun

Needs Python 3 with numpy, shapely (2.x), pyproj, rasterio, scipy, matplotlib, Pillow and fontTools, xelatex (TeX Gyre Pagella, Inter) and pdftotext, and node with Playwright for the QA screenshots. Raw inputs (paths in `code/common.py`, or set `WI_COAST`, `WI_GEO`, `WI_RAW`):

- GSHHG: `pip download basemap-data basemap-data-hires` (2.0.0) and unpack `mpl_toolkits/basemap_data/gshhs_*.dat` and `gshhsmeta_*.dat`.
- WorldPop tiles: `docs/tiles/L3/` (957 files and `_meta.json`) from https://github.com/nn0000asdf/world-population-3d, retrieved in 2026.
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
- Sweden's official count of 267,570 islands: Statistics Sweden (2013), quoted for comparison.
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Where the world's islands are: counting, measuring and peopling every island in the GSHHG shoreline. Zenodo. https://doi.org/{10.5281/zenodo.23848301}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
