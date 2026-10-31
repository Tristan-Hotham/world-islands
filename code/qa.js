// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8792; set PORT to change).
const { chromium } = require("playwright");
// Leaflet from a local npm copy (the CDN is not reachable from the build container); base tiles and fonts are blocked here.
const LEAF = process.env.LEAFLET_DIST || "/dev/shm/football/npm/node_modules/leaflet/dist";
(async () => {
  const b = await chromium.launch();
  const errs = [];
  for (const [nm, vw, vh] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/leaflet.min.js/, r => r.fulfill({ path: LEAF + "/leaflet.js" }));
    await p.route(/leaflet.min.css/, r => r.fulfill({ path: LEAF + "/leaflet.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::/.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    p.on("response", r => { if (r.status() >= 400) errs.push(nm + " http " + r.status() + " " + r.url()); });
    await p.goto("http://localhost:" + (process.env.PORT || 8792) + "/index.html", { waitUntil: "networkidle" });
    await p.waitForTimeout(3000);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(800); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png` }); };
    await shot("#atlas", "map");
    await p.click("#focusRow .btn:nth-child(4)"); await p.waitForTimeout(2500); await shot("#atlas", "baltic");
    await p.evaluate(() => { map.setView([59.45, 18.75], 10); }); await p.waitForTimeout(2000);
    const box = await p.locator("#map").boundingBox(); await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2); await p.waitForTimeout(800); await shot("#atlas", "closeup_click");
    await p.fill("#q", "Java"); await p.waitForTimeout(500); await p.keyboard.press("Enter"); await p.waitForTimeout(2500); await shot("#atlas", "search_java");
    await p.fill("#q", "Indonesia"); await p.waitForTimeout(500); await p.keyboard.press("Enter"); await p.waitForTimeout(2500); await shot("#atlas", "search_indonesia");
    for (const c of ["sizeChart", "resChart", "ctyChart", "bigChart", "popChart", "regChart", "ceChart", "cards"]) await shot("#" + c, c);
    if (nm === "phone") {
      await p.click("#theme"); await p.waitForTimeout(1500); await shot("#atlas", "dark_map"); await shot("#popChart", "dark_pop");
      await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    } else {
      await p.locator(".lyrBtn").scrollIntoViewIfNeeded(); await p.click(".lyrBtn"); await p.waitForTimeout(500); await shot("#atlas", "layers");
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
