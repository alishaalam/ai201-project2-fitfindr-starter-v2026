"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

See README.md's Tool Inventory for the full contract each one is built to.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── shared helpers ────────────────────────────────────────────────────────────

_SIZE_ALIASES = {
    "m": {"s/m", "m/l"},
    "oversized": {"xl"},
    "baggy": {"xl"},
    "petite": {"s"},
    "tiny": {"s"},
}


def _describe_item(item: dict) -> str:
    brand = f" by {item['brand']}" if item.get("brand") else ""
    return (
        f"{item['title']}{brand} — category: {item['category']}, "
        f"colors: {', '.join(item['colors'])}, style: {', '.join(item['style_tags'])}"
    )


def _format_price(item: dict) -> str:
    return f"${item['price']:g}"


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def _normalize_size(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"\(.*?\)", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _size_matches(requested: str, listing_size: str) -> bool:
    req, lst = _normalize_size(requested), _normalize_size(listing_size)
    if req == lst:
        return True
    return lst in _SIZE_ALIASES.get(req, ()) or req in _SIZE_ALIASES.get(lst, ())


def _tokenize(text: str) -> list[str]:
    return re.sub(r"[^\w\s]", " ", text.lower()).split()


def _listing_tokens(item: dict) -> set[str]:
    text = " ".join([item["title"], item["description"], " ".join(item["style_tags"])])
    return set(_tokenize(text))


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    Args:
        description: keywords describing what the user wants.
        size:        a size string to filter by, or None to skip size filtering.
                     See README.md's Tool Inventory for the exact match rule.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first by keyword overlap,
        at most config.SEARCH_RESULT_LIMIT of them. Empty list when nothing
        matches — never None, never an exception.
    """
    listings = load_listings()

    candidates = []
    for item in listings:
        if max_price is not None and item["price"] > max_price:
            continue
        if size is not None and not _size_matches(size, item["size"]):
            continue
        candidates.append(item)

    query_tokens = set(_tokenize(description))
    if not query_tokens:
        return []

    scored = [(item, len(query_tokens & _listing_tokens(item))) for item in candidates]
    scored = [(item, s) for item, s in scored if s > 0]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    return [item for item, _ in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

_STYLIST_SYSTEM = (
    "You are a friendly, concise fashion stylist helping someone decide how "
    "to wear a secondhand clothing item they're considering buying. Be "
    "specific and practical. Keep your answer to 3-5 sentences."
)


def _describe_wardrobe_item(w: dict) -> str:
    notes = f" (notes: {w['notes']})" if w.get("notes") else ""
    return (
        f"- {w['name']} [{w['category']}], colors: {', '.join(w['colors'])}, "
        f"style: {', '.join(w['style_tags'])}{notes}"
    )


def _build_general_advice_prompt(new_item: dict) -> str:
    return (
        f"A shopper is considering buying this secondhand item:\n"
        f"{_describe_item(new_item)}\n\n"
        f"They haven't entered a wardrobe yet, so you don't know what else "
        f"they own. Give general styling advice for this piece on its own: "
        f"what colors, categories, and vibes would pair well with it, and "
        f"one or two concrete outfit ideas using generic pieces (e.g. "
        f"'straight-leg jeans' or 'white sneakers') rather than items you "
        f"can't actually see."
    )


def _build_outfit_prompt(new_item: dict, items: list[dict]) -> str:
    wardrobe_lines = "\n".join(_describe_wardrobe_item(w) for w in items)
    return (
        f"A shopper is considering buying this secondhand item:\n"
        f"{_describe_item(new_item)}\n\n"
        f"Here is everything currently in their closet:\n{wardrobe_lines}\n\n"
        f"Suggest 1-2 complete outfits that pair the new item with pieces "
        f"from their closet. Refer to each existing piece by the exact name "
        f"listed above. If nothing in the closet really works, say so "
        f"plainly and name the one category of item they'd need to add."
    )


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  May be empty.

    Returns:
        A non-empty string with outfit suggestions. With an empty wardrobe,
        general styling advice instead — never raises, never returns "".
    """
    items = wardrobe.get("items") or []
    prompt = (
        _build_outfit_prompt(new_item, items)
        if items
        else _build_general_advice_prompt(new_item)
    )

    response = generate(prompt, system=_STYLIST_SYSTEM)
    if response.strip():
        return response

    title = new_item.get("title", "this item")
    return (
        f"Pair the {title} with neutral basics you already own and let it "
        f"be the statement piece — a safe default until you've got more to "
        f"go on."
    )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

_FIT_CARD_SYSTEM = (
    "You write short, casual social-media captions for secondhand fashion "
    "finds — the voice of someone excitedly posting about a thrift pickup "
    "they just found, not a store describing a product for sale."
)


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption mentioning the item, its price, and its
        platform once each. If `outfit` is empty or whitespace, a descriptive
        fallback message instead of calling the model.
    """
    if not outfit or not outfit.strip():
        title = new_item.get("title", "this piece")
        price = _format_price(new_item)
        platform = new_item.get("platform", "the platform")
        return (
            f"No outfit pairing came back for the {title}, but the find "
            f"itself still stands — {price} on {platform} if the fit and "
            f"condition work for you."
        )

    price = _format_price(new_item)
    platform = new_item["platform"]
    prompt = (
        f"Write a 2-4 sentence social media caption for this secondhand find:\n"
        f"Item: {_describe_item(new_item)}\n"
        f"Price: {price}\n"
        f"Platform: {platform}\n"
        f"Outfit idea: {outfit}\n\n"
        f"Write it in the voice of a real person excitedly posting about "
        f"their find — not a product listing, no bullet points. Weave the "
        f"outfit idea in naturally. Mention the price exactly once, written "
        f"as {price}. Mention the platform exactly once, by name "
        f"({platform}). Mention the item itself. Keep the whole caption to "
        f"2-4 sentences."
    )
    return generate(prompt, system=_FIT_CARD_SYSTEM)
