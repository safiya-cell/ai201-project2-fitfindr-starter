"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
   try:
        listings = load_listings()
    except Exception:
     return []
    
    candidates = []
    for listing in listings:
        # Price filter
        if max_price is not None:
            try:
                if float(listing.get("price", 0)) > max_price:
                    continue
            except (TypeError, ValueError):
                continue
 
        # Size filter — substring match so "M" hits "S/M", "M/L", etc.
        if size is not None:
            listing_size = str(listing.get("size", "")).upper()
            if size.upper() not in listing_size:
                continue
 
        candidates.append(listing)
 
    if not candidates:
        return []
    
    return candidates

 # 3. Score by keyword overlap
    keywords = _tokenize(description)
    if not keywords:
        return candidates  # nothing to score on; return all filtered results
 
    scored = [(s, l) for l in candidates if (s := _score_listing(l, keywords)) > 0]
 
    # 4 & 5. Zero-score listings already dropped; sort highest first
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored]
    return []


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    item_name   = new_item.get("title", "this item")
    item_tags   = ", ".join(new_item.get("style_tags", [])) or "no tags"
    item_colors = ", ".join(new_item.get("colors", [])) or "unknown"
    item_cat    = new_item.get("category", "clothing")
 
    # 1. Check whether the wardrobe is empty
    wardrobe_items = wardrobe.get("items", [])
 
    # 2. Empty wardrobe — ask for general styling advice
    if not wardrobe_items:
        prompt = (
            f"A user is considering buying: '{item_name}' "
            f"(category: {item_cat}, colors: {item_colors}, style: {item_tags}).\n\n"
            "Their wardrobe is empty, so you can't reference specific pieces they own. "
            "Give 1–2 outfit ideas that pair well with this item — suggest the types "
            "of bottoms, tops, shoes, or accessories that would complete the look. "
            "Be specific about silhouettes, colors, and vibes. Keep it to 3–5 sentences."
        )
        return _llm(prompt)
 
    # 3. Non-empty wardrobe — format pieces and ask for specific pairings
    wardrobe_lines = "\n".join(
        f"- {item.get('title', 'Unknown')} "
        f"(colors: {', '.join(item.get('colors', []))}, "
        f"style: {', '.join(item.get('style_tags', []))})"
        for item in wardrobe_items
    )
 
    prompt = (
        f"A user is considering buying: '{item_name}' "
        f"(category: {item_cat}, colors: {item_colors}, style: {item_tags}).\n\n"
        f"Their current wardrobe includes:\n{wardrobe_lines}\n\n"
        "Suggest 1–2 complete outfits that pair the new item with pieces from "
        "their wardrobe. Name the specific wardrobe pieces you're using in each "
        "outfit and explain briefly why they work together (color, silhouette, vibe). "
        "Keep it to 4–6 sentences total."
    )
 
    # 4. Return LLM response
    return _llm(prompt)
    client = _get_groq_client()
    # Describe the new item for the prompt regardless of wardrobe state.
    item_summary = (
        f"Title: {new_item.get('title', 'Unknown')}\n"
        f"Category: {new_item.get('category', 'unknown')}\n"
        f"Colors: {', '.join(new_item.get('colors', [])) or 'unknown'}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', [])) or 'none'}\n"
        f"Condition: {new_item.get('condition', 'unknown')}\n"
        f"Price: ${new_item.get('price', '?')}"
    )
 
    # 1. Check whether wardrobe['items'] is empty.
    # .get() with a default handles both a missing key and an explicit empty list
    # without raising a KeyError.
    wardrobe_items = wardrobe.get("items", [])
 
    if not wardrobe_items:
        # 2. Empty wardrobe: ask for general styling ideas without referencing
        # any pieces the user owns, since there are none.
        prompt = (
            "You are a knowledgeable thrift-fashion stylist.\n\n"
            "A user is considering buying this secondhand item:\n"
            f"{item_summary}\n\n"
            "Their wardrobe is empty, so do not reference any pieces they own. "
            "Suggest 1-2 outfit ideas that would pair well with this item. "
            "For each outfit, name the types of pieces that would complete the look "
            "(for example: 'wide-leg trousers', 'chunky platform boots'), describe the "
            "overall vibe, and explain briefly why the combination works. "
            "Keep the response to 4-6 sentences."
        )
    else:
        # 3. Non-empty wardrobe: format each piece and ask the LLM to build
        # specific outfit combinations using items the user already owns.
        wardrobe_lines = "\n".join(
            "- {title} (category: {cat}, colors: {colors}, style: {style})".format(
                title=item.get("title", "Unknown"),
                cat=item.get("category", "?"),
                colors=", ".join(item.get("colors", [])) or "?",
                style=", ".join(item.get("style_tags", [])) or "?",
            )
            for item in wardrobe_items
        )
        prompt = (
            "You are a knowledgeable thrift-fashion stylist.\n\n"
            "A user is considering buying this secondhand item:\n"
            f"{item_summary}\n\n"
            "Their current wardrobe contains:\n"
            f"{wardrobe_lines}\n\n"
            "Suggest 1-2 complete outfits that pair the new item with pieces already "
            "in their wardrobe. For each outfit, name the exact wardrobe pieces you are "
            "using, describe the overall vibe, and give a brief reason why the combination "
            "works (color, silhouette, or style). Keep the response to 4-6 sentences."
        )
 
    # 4. Call the LLM and return its response as a plain string.
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
 
    return ""


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
       # 1. Guard against empty/whitespace outfit
    if not outfit or not outfit.strip():
        return (
            "Could not generate a fit card — outfit data was missing or incomplete. "
            "Try running suggest_outfit first and pass its result here."
        )
 
    item_name     = new_item.get("title", "this find")
    item_price    = new_item.get("price", "unknown price")
    item_platform = new_item.get("platform", "a thrift platform")
 
  # Return an informative message rather than calling the LLM with bad input.
    if not outfit or not outfit.strip():
        return (
            "Error: no outfit description was provided. "
            "Run suggest_outfit() first and pass its result to create_fit_card()."
        )
 
    client = _get_groq_client()

    # 2. Build prompt with item details, outfit context, and caption guidelines
    item_name = new_item.get("title", "this find")
    item_price = new_item.get("price", "?")
    item_platform = new_item.get("platform", "a resale app")

    prompt = (
        "You are writing a casual, authentic OOTD caption for Instagram or TikTok.\n\n"
        f"The outfit: {outfit}\n\n"
        f"The thrifted item: {item_name}, found for ${item_price} on {item_platform}.\n\n"
        "Write a 2-4 sentence caption that:\n"
        "- Sounds like a real person posting, not a brand or product listing\n"
        "- Mentions the item name, price, and platform once each, woven in naturally\n"
        "- Names the specific vibe of the outfit (e.g. 'clean 90s streetwear', "
        "'soft grunge', 'coastal grandma meets Y2K')\n"
        "- Avoids filler phrases like 'slaying', 'obsessed', or 'this look'\n"
        "Return only the caption text. No hashtags. No preamble."
    )
 
   # 3. Call the LLM at high temperature so repeated calls produce varied captions.
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.2,
    )
    return response.choices[0].message.content.strip()
    return ""
  
