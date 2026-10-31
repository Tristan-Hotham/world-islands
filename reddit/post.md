# Reddit post (r/dataisbeautiful)

**Title:** [OC] A detailed open map of the world's shorelines has 181,588 islands, and 841 million people (10.3% of humanity) live on one

**Image:** reddit/world_islands.png

**Body:**

I counted every island in GSHHG, the free full-resolution world shoreline used inside a lot of mapping software, and gave each one a size, a country and a population (WorldPop, 2025).

- 181,588 islands, but 52% are under 0.1 km². 23,150 are 1 km² or more.
- The total depends on the map: the crude version of the same shoreline has 762 islands, Natural Earth 10m has 9,628. Islands over 1 km² barely change between the finer versions.
- Canada has the most at every threshold (4,048 of 1 km² or more).
- Java alone has 153.2 million people, more than all of Europe's islands combined, Great Britain included.
- Largest island in a lake on an island: Glover Island, Newfoundland (163 km²).

Interactive map (search any country, click any island): https://maps.tristanhotham.com/world-islands/

**Source comment:**

Data: GSHHG 2.3 full-resolution shorelines (Wessel and Smith, LGPL-3.0); WorldPop Global 2, 2025 constrained estimate at about 1 km (CC BY 4.0), via the world-population-3d tiles on GitHub; Natural Earth (public domain). Tools: Python (shapely, rasterio, matplotlib). Islands are all land except the five continents, plus islands in lakes and around Antarctica. Caveats: counts under 1 km² depend on resolution; the shoreline joins Manhattan and Mumbai's Salsette Island to the mainland; WorldPop is a model and misses some tiny settlements. Paper, data and code: https://github.com/Tristan-Hotham/world-islands
