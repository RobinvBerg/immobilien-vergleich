#!/usr/bin/env python3
"""Patch mallorca-ranking-v3.html to add budget scoring."""
import re

f = '/Users/robin/.openclaw/workspace/mallorca-projekt/html/mallorca-ranking-v3.html'
html = open(f, 'r').read()

# 1. Add budget weight entry
html = html.replace(
    "{id:'bewirt',label:'Bewirtschaftung',val:5},\n];",
    "{id:'bewirt',label:'Bewirtschaftung',val:5},\n  {id:'budget',label:'Budget-Score',val:15},\n];"
)

# 2. Add budget thresholds after andratx dealbreaker thresholds
html = html.replace(
    "{id:'and_w',label:'Gewicht Andratx %',val:20,min:0,max:100},\n];",
    "{id:'and_w',label:'Gewicht Andratx %',val:20,min:0,max:100},\n  {id:'bu_ideal',label:'Budget Ideal (M€)',val:2.0,min:0.5,max:8,step:0.1},\n  {id:'bu_max',label:'Budget Max (M€)',val:3.5,min:0.5,max:10,step:0.1},\n];"
)

# 3. Add budgetScore function after destScore
html = html.replace(
    "function compute() {",
    """function budgetScore(preis, idealM, maxM) {
  const ideal = idealM * 1e6, max = maxM * 1e6;
  if(preis <= 0) return 0;
  if(preis <= ideal) return 100;
  if(preis >= max) return 0;
  return 100 * (1 - (preis - ideal) / (max - ideal));
}

function compute() {"""
)

# 4. Compute sBu for each property (after sBw line)
html = html.replace(
    "return {...o, sZi, sEr, sGr, sCh, sVm, sRe, sBw, _val:null};",
    "const sBu = budgetScore(o.preis, getT('bu_ideal'), getT('bu_max'));\n    return {...o, sZi, sEr, sGr, sCh, sVm, sRe, sBw, sBu, _val:null};"
)

# 5. Update score formula to include budget
html = html.replace(
    "o.score = (o.sZi*getW('zimmer') + o.sEr*getW('erreich') + o.sGr*getW('grund')\n      + o.sCh*getW('charme') + o.sVm*getW('vermiet') + o.sVa*getW('value')\n      + o.sRe*getW('reno') + o.sBw*getW('bewirt')) / (total||1);",
    "o.score = (o.sZi*getW('zimmer') + o.sEr*getW('erreich') + o.sGr*getW('grund')\n      + o.sCh*getW('charme') + o.sVm*getW('vermiet') + o.sVa*getW('value')\n      + o.sRe*getW('reno') + o.sBw*getW('bewirt') + o.sBu*getW('budget')) / (total||1);"
)

# 6. Add budget score bar to card display - find where score bars are rendered
# Look for sVa display and add sBu after it
html = html.replace(
    """<div class="sb"><span>P/L</span><div class="bar"><div style="width:${o.sVa.toFixed(0)}%"></div></div><span>${o.sVa.toFixed(0)}</span></div>""",
    """<div class="sb"><span>P/L</span><div class="bar"><div style="width:${o.sVa.toFixed(0)}%"></div></div><span>${o.sVa.toFixed(0)}</span></div>
            <div class="sb"><span>Budget</span><div class="bar"><div style="width:${o.sBu.toFixed(0)}%;background:${o.sBu<30?'#ef5350':o.sBu<70?'#ffa726':'#66bb6a'}"></div></div><span>${o.sBu.toFixed(0)}</span></div>"""
)

open(f, 'w').write(html)
print("Done! All patches applied.")
