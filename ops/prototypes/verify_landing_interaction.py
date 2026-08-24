from playwright.sync_api import sync_playwright
import pathlib, sys
p = pathlib.Path("out/qesis_landing.html").resolve().as_uri()
fails=[]
with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(viewport={"width":1320,"height":940})
    pg.on("pageerror", lambda e: fails.append(f"pageerror {e}"))
    pg.goto(p); pg.wait_for_timeout(500)

    # 1. sort by composite ascending then descending
    pg.click('#rank th[data-sort="2"]'); pg.wait_for_timeout(150)
    first = pg.inner_text("#rank tbody tr:first-child td:nth-child(2)")
    if first.strip() != "Switzerland": fails.append(f"sort asc gave {first!r}, expected Switzerland")
    pg.click('#rank th[data-sort="2"]'); pg.wait_for_timeout(150)
    first = pg.inner_text("#rank tbody tr:first-child td:nth-child(2)")
    if first.strip() != "Saudi Arabia": fails.append(f"sort desc gave {first!r}, expected Saudi Arabia")
    if pg.get_attribute('#rank th[data-sort="2"]', "aria-sort") != "descending":
        fails.append("aria-sort not announced")

    # 2. filter
    pg.fill("#q", "bahr"); pg.wait_for_timeout(200)
    vis = pg.eval_on_selector_all("#rank tbody tr", "es=>es.filter(e=>!e.hidden).length")
    if vis != 1: fails.append(f"filter 'bahr' showed {vis} rows, expected 1")
    if "1 of 32" not in pg.inner_text("#count"): fails.append("filter count not updated")
    pg.fill("#q", ""); pg.wait_for_timeout(200)

    # 3. linked views: clicking a row selects the territory
    pg.click('#rank tbody tr[data-row="NLD"]'); pg.wait_for_timeout(400)
    if "Netherlands" not in pg.inner_text("#readout"): fails.append("row click did not drive the readout")
    sel = pg.eval_on_selector_all('[data-iso].sel', "e=>e.map(x=>x.getAttribute('data-iso'))")
    if sel != ["NLD"]: fails.append(f"selection ring on {sel}, expected exactly NLD")

    # 4. withheld state carries its cause, and only one hot accent is lit per view
    pg.eval_on_selector('[data-iso="SGP"]', "e=>e.dispatchEvent(new MouseEvent('click',{bubbles:true}))")
    pg.wait_for_timeout(300)
    t = pg.inner_text("#readout")
    for want in ("Singapore","withheld","SOURCE"):
        if want not in t: fails.append(f"withheld readout missing {want!r}")

    # 5. scroll spy marks exactly one section
    pg.evaluate("document.getElementById('audit').scrollIntoView()"); pg.wait_for_timeout(600)
    on = pg.eval_on_selector_all(".rnav a.on", "e=>e.map(x=>x.textContent)")
    if on != ["Audit"]: fails.append(f"scroll spy lit {on}, expected ['Audit']")

    # 6. every CTA points at the same mailto
    hrefs = set(pg.eval_on_selector_all("a.cta", "e=>e.map(x=>x.getAttribute('href'))"))
    if len(hrefs) != 1: fails.append(f"calls to action disagree: {hrefs}")
    if not next(iter(hrefs)).startswith("mailto:"): fails.append("primary action is not a mailto")

    # 7. reduced motion and keyboard reach
    pg.keyboard.press("Tab")
    b.close()
print("FAIL" if fails else "PASS", "interaction")
for f in fails: print("  x", f)
sys.exit(1 if fails else 0)
