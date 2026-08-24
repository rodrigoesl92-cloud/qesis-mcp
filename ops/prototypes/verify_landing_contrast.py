"""Contrast audit against the rendered page, not against the stylesheet."""
from playwright.sync_api import sync_playwright
import pathlib, sys
def lin(c): return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
def lum(rgb): r,g,b=[lin(v/255) for v in rgb]; return .2126*r+.7152*g+.0722*b
def parse(s):
    n=[float(x) for x in s[s.index("(")+1:s.index(")")].replace(","," ").split()[:3]]
    return tuple(n)
def cr(a,b):
    L=sorted([lum(a),lum(b)],reverse=True); return (L[0]+.05)/(L[1]+.05)

SEL = [".eyebrow--hot",".tier--pick b",".chip",".src",".rtag",".rnav a",".fam span",
       ".tri span",".tri i",".mini dd",".why",".readout dd",".readout dt",
       ".count",".filter",".cardnum",".alt",".lede","p",".cta"]
fails=[]
with sync_playwright() as pw:
    b=pw.chromium.launch()
    for sch in ("light","dark"):
        pg=b.new_page(color_scheme=sch,viewport={"width":1320,"height":940})
        pg.goto(pathlib.Path("out/qesis_landing.html").resolve().as_uri()); pg.wait_for_timeout(400)
        for s in SEL:
            r=pg.evaluate("""(sel)=>{const e=document.querySelector(sel); if(!e) return null;
              const cs=getComputedStyle(e); let p=e, bg='rgba(0, 0, 0, 0)';
              while(p){const c=getComputedStyle(p).backgroundColor;
                if(c && !c.startsWith('rgba(0, 0, 0, 0')){bg=c;break;} p=p.parentElement;}
              const fs=parseFloat(cs.fontSize), fw=parseInt(cs.fontWeight)||400;
              return {fg:cs.color,bg,fs,fw};}""", s)
            if not r: continue
            ratio=cr(parse(r["fg"]),parse(r["bg"]))
            large = r["fs"]>=24 or (r["fs"]>=18.66 and r["fw"]>=700)
            need = 3.0 if large else 4.5
            mark = "ok " if ratio>=need else "FAIL"
            if ratio<need: fails.append(f"{sch} {s}: {ratio:.2f} against {need} at {r['fs']:.0f}px")
            print(f"  {mark} {sch:5s} {s:16s} {ratio:5.2f}  need {need}  {r['fs']:.0f}px")
        pg.close()
    b.close()
print()
print(("FAIL, %d" % len(fails)) if fails else "PASS: every text pair meets WCAG AA at its rendered size")
for f in fails: print("  x", f)
sys.exit(1 if fails else 0)
