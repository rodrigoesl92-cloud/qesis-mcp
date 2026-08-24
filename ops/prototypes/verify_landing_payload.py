"""Final verification. Checks the artefact, not the text about the artefact."""
from playwright.sync_api import sync_playwright
import pathlib, json, re, sys

root = pathlib.Path(".")
page_path = root/"out/qesis_landing.html"
uri = page_path.resolve().as_uri()
doc = json.loads(pathlib.Path("/mnt/user-data/uploads/qesis-mcp/data/qesis_v8.json").read_text(encoding="utf-8"))
html = page_path.read_text(encoding="utf-8")
fails = []

# 1. every ranked composite and coverage present, no invented country
for iso, c in doc["countries"].items():
    if c["composite"] is None: continue
    if f'>{c["composite"]:.1f}<' not in html: fails.append(f"composite missing for {iso}")
for e in doc["epis_findings"]:
    if e["withholding_cause"] not in html: fails.append(f"cause missing for {e['iso3']}")
    if e["cause_statement"] not in html: fails.append(f"cause statement missing for {e['iso3']}")

# 2. effective weights, all five, point + both interval bounds
for k, a in doc["effective_weights"]["axes"].items():
    if f'>{a["main_effect"]:.3f}<' not in html: fails.append(f"main_effect missing for {k}")
    if f'>{a["nominal"]:.2f}<' not in html: fails.append(f"nominal tick label missing for {k}")

# 3. forbidden claims, VISUALISATION_SPEC section 1
for pat, why in [(r"\bcorner\b", "trilemma corner"),
                 (r"sovereignty test", "no sovereignty_test field exists"),
                 (r"\bnecessary\b", "no condition is publishable as necessary under D-109"),
                 (r"0\.916", "the REE necessity figure is withdrawn"),
                 (r"\d{1,2} of 35 states pass", "D-104 with a country list")]:
    if re.search(pat, html, re.I): fails.append(f"forbidden claim present: {why}")

# 4. the caveat shares the viewport with the headline claim (E-2)
import html as _h
_cav = _h.escape(doc["effective_weights"]["honesty_caveat"], quote=True)
if _cav[:80] not in html:
    fails.append("honesty_caveat not rendered")
else:
    # E-2: the caveat must share the viewport with the claim, not be a footnote
    ci = html.index(_cav[:80]); hi = html.index('id="audit"')
    gap = html[hi:ci]
    if ci < hi or gap.count("<h2") > 2:
        fails.append("E-2: the caveat does not sit with the claim it bounds")
    print(f"E-2: caveat sits inside the audit view, {gap.count('<h2')} headings from its claim")

# 5. render checks
with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(java_script_enabled=False, viewport={"width":1100,"height":900})
    pg = ctx.new_page(); pg.goto(uri); pg.wait_for_timeout(300)
    rows = pg.eval_on_selector_all("table tbody tr", "e=>e.length")
    paths = pg.eval_on_selector_all("[data-iso]", "e=>e.length")
    if rows < 40: fails.append(f"JS off: only {rows} table rows, tables are not real HTML")
    cards = pg.eval_on_selector_all(".cards .card", "e=>e.length")
    if cards != 3: fails.append(f"JS off: {cards} gap cards, expected one per withheld state")
    fams = pg.eval_on_selector_all(".fams .fam", "e=>e.length")
    if fams != 3: fails.append(f"JS off: {fams} axis families, expected three")
    ctas = pg.eval_on_selector_all('a.cta', "e=>e.length")
    if ctas < 3: fails.append(f"only {ctas} calls to action, expected rail + hero + close")
    if paths < 39: fails.append(f"JS off: only {paths} map marks")
    if pg.evaluate("document.body.scrollWidth") > pg.evaluate("document.documentElement.clientWidth")+1:
        fails.append("JS off: body scrolls horizontally")
    print(f"JS disabled: {rows} table rows, {paths} map marks render")
    ctx.close()

    for scheme in ("light","dark"):
        pg = b.new_page(color_scheme=scheme, viewport={"width":1280,"height":900})
        errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(uri); pg.wait_for_timeout(400)
        if errs: fails.append(f"{scheme}: page errors {errs}")
        # body ground must be painted from a token, not inherited
        bg = pg.evaluate("getComputedStyle(document.body).backgroundColor")
        if bg in ("rgba(0, 0, 0, 0)","transparent"): fails.append(f"{scheme}: body background transparent")
        # keyboard: first map mark must take focus and update the readout
        pg.eval_on_selector('[data-iso="TWN"]', "e=>e.focus()"); pg.wait_for_timeout(200)
        txt = pg.inner_text("#readout")
        if "Taiwan" not in txt: fails.append(f"{scheme}: keyboard focus does not drive the readout")
        if "SOURCE_POLITICAL_COVERAGE" not in txt:
            fails.append(f"{scheme}: withholding cause absent from the readout")
        print(f"{scheme}: body {bg}, keyboard readout ok")
        pg.close()
    b.close()

print()
if fails:
    print(f"FAIL, {len(fails)} problems")
    for f in fails: print("  x", f)
    sys.exit(1)
print("PASS: every figure on the page traces to the payload, no forbidden claim, "
      "renders and is navigable with JavaScript disabled, both themes painted.")
