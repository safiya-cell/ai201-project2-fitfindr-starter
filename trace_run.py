"""
trace_run.py

Runs the example query from planning.md step by step and verifies that
state flows correctly through the session dict — no hardcoded values,
no re-prompting between steps.

Run from the project root:
    python trace_run.py
"""

from agent import run_agent, _parse_query
from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe

SEP  = "=" * 60
DASH = "-" * 60

QUERY   = "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers."
WARDROBE = get_example_wardrobe()


def check(label: str, passed: bool) -> None:
    print(f"  [{'PASS' if passed else 'FAIL'}] {label}")


# ── Step 2: parse query ───────────────────────────────────────────────────────

print(SEP)
print("Step 2 — _parse_query")
print(SEP)
parsed = _parse_query(QUERY)
print(f"  description : {parsed['description']!r}")
print(f"  size        : {parsed['size']!r}")
print(f"  max_price   : {parsed['max_price']!r}")
check("description is a non-empty string",
      isinstance(parsed["description"], str) and bool(parsed["description"].strip()))
check("max_price is 30.0",
      parsed["max_price"] == 30.0)
check("size is None (no size in query)",
      parsed["size"] is None)


# ── Step 3: search_listings ───────────────────────────────────────────────────

print()
print(SEP)
print("Step 3 — search_listings")
print(SEP)
results = search_listings(
    description=parsed["description"],
    size=parsed["size"],
    max_price=parsed["max_price"],
)
print(f"  {len(results)} result(s) returned")
for i, r in enumerate(results[:3]):
    print(f"  [{i}] {r['title']} — ${r['price']} · {r['platform']} · size {r['size']}")
check("at least one result returned", len(results) > 0)
check("every result is within the $30 price limit",
      all(r["price"] <= 30.0 for r in results))

# Capture the top result so we can check identity later
manual_selected = results[0]
print(f"\n  selected_item will be results[0]: {manual_selected['title']!r} (id={manual_selected['id']!r})")


# ── Step 5: suggest_outfit ────────────────────────────────────────────────────

print()
print(SEP)
print("Step 5 — suggest_outfit")
print(SEP)
print(f"  new_item : {manual_selected['title']!r}")
print(f"  wardrobe items: {[i['title'] for i in WARDROBE.get('items', [])]}")
manual_outfit = suggest_outfit(new_item=manual_selected, wardrobe=WARDROBE)
print(f"\n  outfit_suggestion (first 200 chars):\n  {manual_outfit[:200]!r}")
check("outfit_suggestion is a non-empty string",
      isinstance(manual_outfit, str) and bool(manual_outfit.strip()))


# ── Step 6: create_fit_card ───────────────────────────────────────────────────

print()
print(SEP)
print("Step 6 — create_fit_card")
print(SEP)
print(f"  outfit arg  : session['outfit_suggestion'] (first 80 chars): {manual_outfit[:80]!r}")
print(f"  new_item arg: session['selected_item']: {manual_selected['title']!r}")
manual_fitcard = create_fit_card(outfit=manual_outfit, new_item=manual_selected)
print(f"\n  fit_card:\n  {manual_fitcard!r}")
check("fit_card is a non-empty string",
      isinstance(manual_fitcard, str) and bool(manual_fitcard.strip()))


# ── Full run_agent: confirm session keys match the manual trace ───────────────

print()
print(SEP)
print("run_agent() — confirming session keys match the manual trace above")
print(SEP)
session = run_agent(query=QUERY, wardrobe=WARDROBE)

si = session["selected_item"]
print(f"  session['error']            : {session['error']!r}")
print(f"  session['selected_item']['id']: {si['id'] if si else None!r}")
print(f"  session['outfit_suggestion'] (first 80): {(session['outfit_suggestion'] or '')[:80]!r}")
print(f"  session['fit_card'] (first 80)          : {(session['fit_card'] or '')[:80]!r}")

check("no error on success path", session["error"] is None)

# State-flow check 1: selected_item is results[0], not a different or hardcoded item
check("session['selected_item']['id'] matches manual results[0]",
      si is not None and si["id"] == manual_selected["id"])
check("session['selected_item']['title'] matches manual results[0]",
      si is not None and si["title"] == manual_selected["title"])

# State-flow check 2: outfit_suggestion is non-empty and item details reached the LLM
check("session['outfit_suggestion'] is non-empty",
      bool((session["outfit_suggestion"] or "").strip()))
item_keyword = manual_selected["title"].split()[0].lower()  # e.g. "vintage"
brand = manual_selected.get("brand", "").lower()
full_text = (session["outfit_suggestion"] + session["fit_card"]).lower()
check(f"item keyword {item_keyword!r} or brand {brand!r} appears in LLM output "
      "(item details flowed into prompts, not hardcoded)",
      item_keyword in full_text or brand in full_text)

# State-flow check 3: fit_card is non-empty
check("session['fit_card'] is non-empty",
      bool((session["fit_card"] or "").strip()))

# State-flow check 4: price filter was respected end-to-end
check("selected_item price <= $30 (price filter honoured end-to-end)",
      si is not None and si["price"] <= 30.0)


# ── No-results path ───────────────────────────────────────────────────────────

print()
print(SEP)
print("No-results path — 'designer ballgown size XXS under $5'")
print(SEP)
s2 = run_agent(query="designer ballgown size XXS under $5", wardrobe=WARDROBE)
print(f"  session['error']           : {s2['error']!r}")
print(f"  session['selected_item']   : {s2['selected_item']!r}")
print(f"  session['outfit_suggestion']: {s2['outfit_suggestion']!r}")
print(f"  session['fit_card']         : {s2['fit_card']!r}")

check("error message is set", bool(s2["error"]))
check("selected_item is None — no item picked on error path",
      s2["selected_item"] is None)
check("outfit_suggestion is None — suggest_outfit NOT called on error path",
      s2["outfit_suggestion"] is None)
check("fit_card is None — create_fit_card NOT called on error path",
      s2["fit_card"] is None)
check("error message contains query context (not generic)",
      any(w in (s2["error"] or "").lower()
          for w in ["ballgown", "xxs", "5", "no listings", "found"]))

print()
print(SEP)
print("Trace complete. Fix any FAIL lines before submitting.")
print(SEP)