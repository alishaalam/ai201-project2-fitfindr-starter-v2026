# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr is a secondhand-clothes shopping agent. A user types a plain-language request such as "vintage graphic tee under $30" (optionally with a size), and the agent searches a listings dataset, picks the best match, suggests outfits that pair it with pieces from the user's wardrobe, and writes a short shareable "fit card" caption. If nothing matches, it stops before the outfit step and tells the user which filters to loosen.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Searches the listings dataset for items matching a text description, with optional size and max-price filters, and returns the best matches, ranked by matched keywords weighted by how rare each word is across the catalog (so an item word like `sneakers` outranks a colour like `black`; ties keep file order).
- **Inputs:** `description` (str) — keywords describing what the user wants, e.g. `"vintage graphic tee"`. `size` (str | None, default `None`) — a size to filter by; `None` skips size filtering. Match rule: normalize both the requested size and each listing's size (lowercase, strip whitespace, drop any parenthetical like `"(fits oversized)"`), then match if they're equal OR both appear together in a small fixed alias table (e.g. `"m"` aliases to `"s/m"` and `"m/l"`, `"oversized"`/`"baggy"` alias to `"xl"`, `"petite"`/`"tiny"` alias to `"s"`) — no substring matching, so `"l"` never matches `"xl"`. Shoe sizes (`US 7`–`US 9`) and waist sizes (`W27`–`W32`, `W30 L30`) match only on exact equality after normalization, with no aliasing to the letter scale. A size term with no entry in the alias table (e.g. a relative description like `"big feet"`) is not parsed into `size` at all — it stays in `description`, where it only affects keyword-overlap ranking, not filtering. `max_price` (float | None, default `None`) — maximum price, inclusive; `None` skips price filtering.
- **Returns:** A `list[dict]` of matching listings, best match first. Each dict has `id, title, description, category, style_tags (list[str]), size, condition, price (float), colors (list[str]), brand (str or None), platform`.
- **When it has nothing:** An empty list — not `None`, and not an exception. That includes a `description` with no word characters (`""`, whitespace, `"!!!"`) and `description=None`: no keywords means nothing to rank on, so the result is `[]` regardless of size or price.

### `suggest_outfit`

- **What it does:** Given a candidate item and the user's wardrobe, asks the model for one or two outfits that pair the new item with pieces the user already owns.
- **Inputs:** `new_item` (dict) — a listing dict (same shape as `search_listings` returns) for the item under consideration. `wardrobe` (dict) — a dict with key `'items'` holding a `list[dict]` of the user's existing pieces; `'items'` may be an empty list.
- **Returns:** A non-empty `str` containing outfit suggestions.
- **When it has nothing:** When `wardrobe['items']` is empty, returns a non-empty string of general styling advice for the item instead — never raises, never returns `""`.

### `create_fit_card`

- **What it does:** Writes a short, shareable caption (2–4 sentences) about the item and the suggested outfit, in the voice of a real post rather than a product listing.
- **Inputs:** `outfit` (str) — the suggestion string returned by `suggest_outfit()`. `new_item` (dict) — the listing dict for the item.
- **Returns:** A 2–4 sentence `str` caption that mentions the item, its price, and its platform exactly once each, and varies across repeated calls on the same input (see `config.TEMPERATURE` / `CACHE_ENABLED`).
- **When it has nothing:** If `outfit` is empty or whitespace-only, returns a descriptive fallback message string instead of raising.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` describing what the user could change (loosen the price, size, or description) and return the session immediately — do not call `suggest_outfit`. Otherwise, take `search_results[0]` as `selected_item` and continue to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::_parse_query`. `max_price` comes from `under|below|less than|max $N`; `size` comes from `size <token>`; those matches are removed, filler words ("looking for", "a", "an", "I want", "find me") are stripped, and the remaining text is `description`.

**What moves through the session:** `query` → `parsed` → `search_results` → `selected_item` → (`wardrobe`, set at session creation) → `outfit_suggestion` → `fit_card`, with `error` short-circuiting everything after it the moment it's set.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'looking for a vintage graphic tee under $30'
  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Pair the Y2K baby tee with your baggy straight-leg jeans, dark wash to balance the fitted top with streetwear proportions, and finish the look with chunky white sneakers. For a slightly edgy transitional outfit, layer your vintage black denim jacket over the tee, keep the same baggy straight-leg jeans, dark wash, and step into your black combat boots.

  Fit card: I am absolutely losing my mind over this butterfly print Y2K baby tee I just scored on depop for only $18! It's giving total vintage fairycore vibes, but I'm definitely gonna balance out the fitted silhouette by styling it with my favorite baggy dark wash straight-leg jeans and chunky white sneakers. Such a good find!

$ python agent.py   # empty-search path
  stopped: Nothing matched "designer ballgown", under $5, size XXS. No listing contains those words, whatever the size or price. This catalog is tops, bottoms, outerwear, shoes and accessories — try a plain item word like 'jacket', 'jeans' or 'sneakers', and drop the size and price on that retry so they don't block it too.
  fit_card is None — it should still be None here
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'price': 18.0, 'size': 'S/M', ...},
 {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'price': 24.0, 'size': 'L', ...},
 {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'price': 15.0, 'size': 'S/M', ...},
 {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'price': 19.0, 'size': 'L', ...},
 {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'price': 27.0, 'size': 'W29', ...},
 {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'price': 26.0, 'size': 'L', ...}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Grab those vintage Levi's—they'll fill the straight-leg gap your dark wash baggy jeans leave open!
For an effortless streetwear look, pair the jeans with your fitted white ribbed tank top, layered
under the slightly cropped vintage black denim jacket, and finish with chunky white sneakers.
Alternatively, tuck the white ribbed tank top into the jeans, cinch them with your brown leather
belt, and throw on the oversized grey crewneck sweatshirt for a cozy, classic vibe.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Still pinching myself over scoring these vintage Levi's 501 jeans on depop for just $38! They're
the absolute best medium wash and fit like an absolute dream. Can't wait to throw them on with
some fresh white sneakers for the ultimate effortless look.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1 — closing a gap in the `search_listings` spec (Milestone 2)**

- *What I asked for:* A review of my `search_listings` spec's size-matching rule before building anything on it. The first version only said "normalize and match via a small alias table", which left open what happens to sizes like `"M (fits oversized)"`, to words like "oversized" or "petite", to shoe and waist sizes, and to relative terms like "big feet".
- *What came back:* Those four gaps, each with a proposed rule.
- *What I changed:* I rewrote the Inputs line in this README (commit `84fca98`). Parentheticals are now dropped before matching. `oversized`/`baggy` alias to `xl` and `petite`/`tiny` alias to `s`. Shoe sizes (`US 7`–`US 9`) and waist sizes (`W27`–`W32`) match on exact equality only. A relative term like "big feet" is never parsed into `size`; it stays in `description` and only affects ranking. I chose that last rule over a guessed numeric threshold because a wrong filter would silently hide listings, while a ranking tweak can't.

**Moment 2 — building the planning loop and stress-testing its empty-search message (Milestone 5)**

- *What I asked for:* `run_agent()` in `agent.py`, following my branch rule: if `search_listings` returns an empty list, set `session["error"]` and return; otherwise continue to `suggest_outfit` and `create_fit_card`, passing every value through the session.
- *What came back:* A `while` loop that inspects the session each pass and runs the next missing step, plus a regex `_parse_query` and an `_empty_message` helper. I ran both example paths. I also wrapped `suggest_outfit` to confirm the item it received was the same object as `session["selected_item"]` (`True`, `lst_002`).
- *What I changed:* I kept the loop as written, but rewrote `_empty_message` in `agent.py` because of the cold read. Claude's verdict on the first message: it named three levers (price, size, keywords) without saying which one caused the miss; "neighbouring size" and the "M also matches S/M" example were no help for `XXS`; and "fewer or more general keywords" pulled in two directions. The new version re-runs `search_listings` with each filter dropped in turn and says which one blocked the search:
  - **Price blocked it:** "10 match without the price cap — the cheapest is $15, so raise your max to at least that."
  - **Size blocked it:** "6 match in other sizes (L, S/M, W29) — try one of those, or leave the size out."
  - **The words blocked it:** "No listing contains those words, whatever the size or price. This catalog is tops, bottoms, outerwear, shoes and accessories — try a plain item word like 'jacket', 'jeans' or 'sneakers', and drop the size and price on that retry so they don't block it too."
  - **No item word at all** (`""`, `"!!!"`, or only filters like `"size M under $50"`): "I didn't get an item to search for — name what you're after, then add any size or price. Try: 'denim jacket size M under $50', 'black sneakers size M under $50' or 'vintage graphic tee size M under $50'." The examples reuse the user's own size and price so they can copy one as-is.
  I checked all four branches by running them, and the happy path still reaches the fit card. The trade-off is up to two extra local searches on an empty result, which is cheap because search is not a model call.
- *What's still imperfect:* the size list for `graphic tee size XXS` includes `W29`, a waist size, because the search ranks on keyword overlap and a bottoms listing shares a word with the query. The suggestion is accurate to what the tool returned but is not a size a tee buyer would want.

**Everything else AI did in this project**

| Milestone | What Claude did | Result |
|---|---|---|
| 2 | Helped draft the three tool specs and the loop branch rule | `a37431a`, then the size gap fixed in `84fca98` |
| 3 | Helped write the five acceptance criteria with targets and reasoning | `3b01e7c`, `criteria.md` |
| 4 | Implemented `search_listings`, `suggest_outfit`, `create_fit_card` in `tools.py` | `6efacd8`; per-tool tests below |
| 5 | Implemented `run_agent`, `_parse_query`, `_empty_message` | `58a1a94` |
| 6 | Filled in this README from verified output (nothing pasted that wasn't run) | this commit |

**Open Questions (empty-search message)**

- **Cold read result (fresh Claude chat, "designer ballgown size XXS under $5" message):** the reader would search "jacket", "jeans" or "sneakers", so it had a concrete next step and was not stuck. It said it would probably carry "under $5" and "XXS" over to the retry, because "whatever the size or price" never says to drop them, and a retry with those filters could come back empty again. It also noted that dresses aren't in the listed categories, so it would waste a search on "dress". Only the words-blocked variant was tested, and a model reading closely is a more charitable reader than a real user skimming on a phone.
- **Fixed after the cold read:** the words-blocked message now also says to drop the size and price when retrying with a new word. I have not re-run the cold read on this final wording.
- **Empty-description case (added after Moment 2):** a description with no word characters used to fall through to the "words blocked" message, which printed `Nothing matched ""` and claimed no listing contains those words. That is false: no keyword was searched. `_empty_message` now checks for it first and returns the "no item word" message above. `search_listings(None)` also returns `[]` instead of raising `AttributeError`. I ran `""`, `"!!!"`, `"?? under $30"`, `"size M under $50"` and a nonsense query through it. I added a diagnostic scenario for it in `scenarios.py` (`"size M under $50"`, criterion 5).
  - *Trade-off:* the message does not say the filters were kept, because each query is parsed fresh and there is no session across turns. The user retypes them; the examples carry them to make that cheap.
  - *Checked:* the nine example queries (three items, each bare / with `size M under $50` / with `under $30`) all return results. `black sneakers size M under $50` returns only 1, so that example is thin.
  - *Not tested:* the new message with the cold-read method or a human reader.
- Still untested: the price-blocked and size-blocked variants, and a human reader.
- The size suggestions can include sizes that don't fit the item type (the `W29` case above).

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

`python run_eval.py --label before_6criteria`, against the **old ranking** (every matched word counts 1), every scenario five times, caching off, nothing changed between tries. Full output: [results/run_2026-10-11_1926_before_6criteria.md](results/run_2026-10-11_1926_before_6criteria.md). 40 model calls. Criteria 1–5 were first run on 2026-10-07 ([results/run_2026-10-07_1815_before.md](results/run_2026-10-07_1815_before.md), 80 model calls, which also holds runs of a fit-card criterion I later removed) and were run again here together with criterion 6, which I added after diagnosing the search-ranking failure (see `criteria.md`). Criteria 1–5 came out 5/5 both times. The pasted output for criteria 1–5 below is from the first run.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item never changes identity mid-pipeline | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The empty-wardrobe path never falls back to nothing | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. A query with filters but no item word says no item was given | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 6. The item word outranks a colour in the search | 5 of 5 | FAIL | FAIL | FAIL | FAIL | FAIL | MISSED (0/5) |

How each was scored:
- **1:** no crash, no `session["error"]`, non-empty `fit_card`. One fixed query, 5 runs.
- **2:** `session["error"]` set, and no `suggest_outfit` or `create_fit_card` step in the trace. One fixed query, 5 runs.
- **3:** the `id` in the `select`, `suggest_outfit` and `create_fit_card` trace steps is the same. One fixed query, 5 runs.
- **4:** no crash, no `session["error"]`, non-empty `outfit_suggestion`. One fixed query with `wardrobe["items"] == []`, 5 runs.
- **5:** `session["error"]` starts with "I didn't get an item to search for", does not contain "Nothing matched", and the trace has no `suggest_outfit` or `create_fit_card` step. One fixed query, 5 runs.
- **6:** the title of `session["selected_item"]` contains the item word `sneakers`. One fixed query (`black sneakers under $60`), 5 runs.

**Real output from one try**, pasted as text, naming the file and function that produced it:

**Criterion 1** — `agent.py::run_agent`, matching query `vintage graphic tee under $30`, try 1. Fit card:

```
Found the absolute cutest Y2K butterfly baby tee on depop for just $18 and I am obsessed! I'm totally planning to style it with my favorite baggy dark-wash jeans and chunky sneakers, and throw on a black denim jacket when it gets chilly. Such a good little throwback piece for the rotation!
```

**Criterion 2** — `agent.py::run_agent` (the branch) and `agent.py::_empty_message`, query `designer ballgown size XXS under $5`, try 1:

```
Nothing matched "designer ballgown", under $5, size XXS. No listing contains those words, whatever the size or price. This catalog is tops, bottoms, outerwear, shoes and accessories — try a plain item word like 'jacket', 'jeans' or 'sneakers', and drop the size and price on that retry so they don't block it too.
```

Trace:

```
[1] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
[2] branch
      →    search_listings returned nothing, stopping before suggest_outfit
```

**Criterion 3** — `agent.py::run_agent`, query `corduroy pants`, try 1. The same `id=lst_005` at all three steps:

```
[1] search_listings (via MCP)
      in:  description='corduroy pants', size=None, max_price=None
      out: 2 items: Corduroy Wide-Leg Pants — Rust, Low-Rise Cargo Pants — Khaki
[2] select
      in:  id=lst_005
      out: Corduroy Wide-Leg Pants — Rust ($32.0, depop)
      →    took search_results[0]
[3] suggest_outfit
      in:  id=lst_005, item='Corduroy Wide-Leg Pants — Rust', wardrobe=10 items
      out: Pair the rust corduroy pants with the fitted white ribbed tank top tucked in, layered under the vintage black …
[4] create_fit_card
      in:  id=lst_005, item='Corduroy Wide-Leg Pants — Rust', outfit='Pair the rust corduroy pants with the fi'…
      out: Look at these vintage rust corduroy wide-leg pants I just scored on depop for $32! They are the ultimate autum…
```

**Criterion 4** — `tools.py::suggest_outfit`, query `denim jacket under $50` with an empty wardrobe, try 1. Outfit suggestion:

```
This cropped Wrangler denim jacket is a versatile streetwear staple that looks amazing paired with high-waisted black straight-leg trousers or an olive green midi skirt to balance the light blue wash. For color pairings, lean into earthy tones like beige and olive, or stick to a classic denim-on-denim look by styling it with darker indigo jeans. Dress it down with a simple white crewneck tee and canvas sneakers for a casual weekend vibe, or layer it over a slip dress with chunky boots for an effortless 90s edge.
```

**Criterion 5** — `agent.py::run_agent` (the branch) and `agent.py::_empty_message`, query `size M under $50`, try 1:

```
I didn't get an item to search for — name what you're after, then add any size or price. Try: 'denim jacket size M under $50', 'black sneakers size M under $50' or 'vintage graphic tee size M under $50'.
```

Trace:

```
[1] search_listings (via MCP)
      in:  description='', size='M', max_price=50.0
      out: [] (empty)
[2] branch
      →    search_listings returned nothing, stopping before suggest_outfit
```

**Criterion 6** — `tools.py::search_listings` (old ranking), run through `agent.py::run_agent`, query `black sneakers under $60`, try 1 (from [results/run_2026-10-11_1926_before_6criteria.md](results/run_2026-10-11_1926_before_6criteria.md)). The selected item was a shirt, on all five tries:

```
selected_item: Oversized Flannel Shirt — Plaid Red/Black ($22.0, thredUp)
```

Trace:

```
[1] search_listings (via MCP)
      in:  description='black sneakers', size=None, max_price=60.0
      out: 8 items: Oversized Flannel Shirt — Plaid Red/Black, Platform Mary Janes — Black Patent, Vintage Graphic Hoodie — Faded Black … +5 more
[2] select
      in:  id=lst_003
      out: Oversized Flannel Shirt — Plaid Red/Black ($22.0, thredUp)
      →    took search_results[0]
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | A matching query completes all three tools | 4 of 5 | MET (5/5) | No crash, no `session["error"]` and a non-empty `fit_card` on all five tries; the five fit cards were all different, so these were five real model answers. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | `session["error"]` was set and there was no `suggest_outfit` or `create_fit_card` step in the trace on all five tries. |
| 3 | The selected item never changes identity mid-pipeline | 5 of 5 | MET (5/5) | The same `id=lst_005` appeared at `select`, `suggest_outfit` and `create_fit_card` in all five traces. |
| 4 | The empty-wardrobe path never falls back to nothing | 5 of 5 | MET (5/5) | Every try returned a non-empty `outfit_suggestion` with no crash, and the five answers were all different. |
| 5 | A query with filters but no item word says no item was given | 5 of 5 | MET (5/5) | Every message started "I didn't get an item to search for", none said "Nothing matched", and there was no tool-2 step. |
| 6 | The item word outranks a colour in the search | 5 of 5 | MISSED (0/5) | All five tries selected the Oversized Flannel Shirt for `black sneakers under $60`; no title contained "sneakers". Read against the 5-of-5 target, 0 passes is a miss. |

**Diagnoses**

Criteria 1–5 were all met, so there is nothing to diagnose in them. I read each count against the original target: 5/5 against a 4-of-5 target for criterion 1, and 5/5 against 5-of-5 for the rest. Criterion 6 missed, and it was added after the first five were measured, so read it as a measurement of one known bug. See below.

**The miss: criterion 6, 0 of 5. Place: a tool, `search_listings`. Mechanism: the ranking.** For `black sneakers under $60`, two sneaker listings are under $60 (lst_019, lst_035), but each matches one query word ("sneakers"), and so does every black item ("black"). The score was the number of matched words, so they all scored 1 and ties fell back to file order, which put the Oversized Flannel Shirt (lst_003) first. The loop then took `search_results[0]` and styled a shirt for someone who asked for sneakers. The loop and the model both did what they were told. The tool handed them the wrong first result, and no criterion had been checking the order of the results. Because search is deterministic, all five tries failed in the same way: one problem, not five.

**Were the targets too low? Yes, for criteria 1–5.** Every one passed on every try, and 0 of 80 model calls failed. A target that can't fail can't tell a solid agent from a lucky one.

**The criterion I'd tighten: criterion 1, from 4 of 5 to 5 of 5.** The 4-of-5 slack was written for a model failure that `agent.py` had no handler for. `ModelUnavailable` has been handled since Milestone 2, and no call failed, so the slack was never used. The risk in 5 of 5 is that one transient API error, which is not the agent's fault, would fail it. I have not changed `criteria.md` for this one.

**One criterion was broken, not just easy: criterion 3.** It measured the wrong thing. The trace ids come from the same session variable that is passed on, so a swapped item could not have shown up. The revision sits under the original in `criteria.md`, with the original left in place. It has not been re-measured.

**What criteria 1–5 didn't cover:** search relevance. That is the gap criterion 6 now measures. It is still one query, so it shows one failure and not that search is good in general.

**Caveat:** pass and fail were scored by a script I wrote, using the rules written under the Run Log — Before table.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path** — `python app.py ask 'looking for a vintage graphic tee under $30' --trace`

```
[1] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[2] select
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
      →    took search_results[0]
[3] suggest_outfit
      in:  item='Y2K Baby Tee — Butterfly Print', wardrobe=10 items
      out: Pair the Y2K baby tee with your baggy straight-leg jeans, dark wash to balance the fitted top with streetwear …
[4] create_fit_card
      in:  item='Y2K Baby Tee — Butterfly Print', outfit='Pair the Y2K baby tee with your baggy st'…
      out: I am absolutely losing my mind over this butterfly print Y2K baby tee I just scored on depop for only $18! It’…
```

**Empty search** — `python app.py ask 'designer ballgown size XXS under $5' --trace`

```
[1] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
[2] branch
      →    search_listings returned nothing, stopping before suggest_outfit
```

**On the MCP move:** I registered `search_listings` in `mcp_server.py` with a description written for a caller who can't see my code (units, result fields, empty-list case) and swapped the first-pass call in `run_agent()` for `call_tool("search_listings", {...})`. Nothing behaved differently: for `"graphic tee"` under $30, the MCP result was identical to the direct call (same 6 listings, same order), and so were three empty cases (`"!!!"`, `jacket` size `XXS`, `jeans` size `W30` under $50). The two diagnostic searches inside `_empty_message()` still call `tools.search_listings` directly; they are part of the empty-search step, not separate loop steps, and routing them through MCP would only add server launches to the failure path.

---

## Failure Modes

Each triggered on purpose, one at a time. What the agent said:

**1. Empty search** — `python app.py ask 'luxury dress under $1'`

```
  Nothing matched "luxury dress", under $1. 1 match without the price cap — the cheapest is $30, so raise your max to at least that.

0 model calls this session
```

**2. Empty wardrobe** — `python app.py ask 'vintage graphic tee under $30' --empty-wardrobe`

```
(running with an empty wardrobe)

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   This pastel butterfly baby tee looks amazing paired with high-waisted, light-wash straight-leg jeans and chunky white sneakers for an effortless Y2K daytime look. To lean into the cottagecore vibe, you can also style it tucked into an olive green or denim midi skirt with comfortable canvas slip-ons. Stick to bottoms in white, light denim, or earthy tones so the pink and purple graphic really pops without competing for attention.

  Fit card: Still screaming because I just scored this dreamy Y2K butterfly baby tee on depop for only $18! It's giving major nostalgia, and I can't wait to throw it on with some high-waisted light-wash straight-leg jeans and chunky white sneakers for the easiest daytime fit. Such a good find!

2 model calls this session, 433 prompt + 156 output tokens
```

**3. Model unavailable** — one character of `GEMINI_API_KEY` changed, then `python app.py ask 'black denim jacket'`

```
Couldn't reach the model, so there's no outfit yet. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. Fix that, then run the same query again.

1 model calls this session
```

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** `tools.py::search_listings` now ranks by matched keywords **weighted by how rare each word is across the 40 listings** (`_word_weights`: `log((N + 1) / (listings containing the word + 1)) + 1`), instead of counting every matched word as 1. The filters, the `[]`-when-nothing-matches contract and the result limit are unchanged.

**Which failure it was meant to fix:** criterion 6, which missed 0 of 5 (see Verdicts and Diagnoses). Place: the tool, `search_listings`. Mechanism: every matched word scored 1, so `black` tied with `sneakers` and file order put the Oversized Flannel Shirt first. That diagnosis is why the change is to the ranking and not to the loop or a prompt.

### Run Log — After

`python run_eval.py --label after_6criteria`, against the **new ranking**, same six scenarios, cache off, 40 model calls. Full output: [results/run_2026-10-11_1929_after_6criteria.md](results/run_2026-10-11_1929_after_6criteria.md).

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item never changes identity mid-pipeline | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The empty-wardrobe path never falls back to nothing | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. A query with filters but no item word says no item was given | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 6. The item word outranks a colour in the search | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Criterion 6, try 1, `tools.py::search_listings` (new ranking), query `black sneakers under $60`:

```
selected_item: Platform Sneakers — White Chunky Sole ($48.0, poshmark)
```

**Did it help, and how do I know:**

**Yes: criterion 6 went from 0 of 5 to 5 of 5, and criteria 1–5 stayed at 5 of 5, so the one change fixed the failure and broke nothing I measured.**

Side by side (before is Run Log — Before above, after is the table in this section):

| Criterion | Target | Before | After |
|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | 5/5 MET | 5/5 MET |
| 2. An impossible query stops before the second tool | 5 of 5 | 5/5 MET | 5/5 MET |
| 3. The selected item never changes identity mid-pipeline | 5 of 5 | 5/5 MET | 5/5 MET |
| 4. The empty-wardrobe path never falls back to nothing | 5 of 5 | 5/5 MET | 5/5 MET |
| 5. A query with filters but no item word says no item was given | 5 of 5 | 5/5 MET | 5/5 MET |
| **6. The item word outranks a colour in the search** | 5 of 5 | **0/5 MISSED** | **5/5 MET** |

- **Criterion 6 was written after the failure was found.** That is the opposite of how the first five were written, so it shows that this one bug is fixed, not that search is good. It is one deterministic query, so its five tries are the same result five times.
- **Nothing else moved.** Criteria 1–5 passed 5/5 before and after, and the top result for every other scenario query is unchanged (lst_002, lst_005, lst_007, and the two empty queries still return nothing).
- **A wider check, separate from the run log.** I ran 40 colour + item queries (e.g. `black sneakers`, `white boots`, `brown cardigan`) through the old and new ranking. A query passes if the top result's title contains the item word.

| | Top result contains the item word |
|---|---|
| Before (every word counts 1) | 21 of 40 |
| After (rarer words weigh more) | 39 of 40 |

  18 queries were fixed and none got worse. `black sneakers` now returns Platform Sneakers first, `black boots` returns Suede Chelsea Boots, and `black dress` returns the Silk Slip Dress. The one miss is `black jacket`, which returns a black leather bomber; that is arguably right, since the title doesn't say "jacket".
- **Limits of this evidence:** I wrote the 40 queries and the "item word in the title" rule myself, so it is a proxy for relevance and not ground truth. It only covers colour + item queries. The check script is not in the repo.
- **A trade-off I haven't tested:** weighting by rarity favours unusual words, so a rare brand or style word in a query could outrank the item word.

---

## What's Still Broken

No criterion is currently missed (all six are 5/5 after the fix). What's left is what the criteria can't see, and a few things I know are weak.

**Search ranking, which is where the one change landed**
- **A rare style word can still beat the item word.** `y2k black dress` returns Platform Mary Janes first and the Silk Slip Dress second, because `y2k` is a rare tag and the rarity weighting that fixed `black sneakers` also rewards it. This is the trade-off I flagged and had not tested; now I have. I would add a bonus for matching the item word in the title, but that is a second change, and the milestone asks for one.
- **Words that aren't in the searched text find nothing.** `shoes` and `trainers` return `[]` even though the catalog has shoes, because the search reads only title, description and style tags, not `category`. The brand isn't searched either: `wrangler jacket` doesn't put the Wrangler denim jacket first, because "Wrangler" is in the `brand` field and not in the text. I would index `category` and `brand` and add a small synonym list, and I stopped because it is a separate change from the weighting.
- **My evidence for the fix is narrow.** Criterion 6 is one query, and I wrote it after finding the bug. The 21 → 39 of 40 check uses queries and a "noun in the title" rule I also wrote, and covers only colour + item queries.

**Measurement**
- **Criterion 3's revision has not been re-measured.** It now asks for the full dict the tools received, captured from the tool calls, but the eval still reads ids from the trace. I would wrap the two tools in the eval to record their arguments. I stopped because the revision was only written this unit.
- **Criterion 1 still says 4 of 5 in `criteria.md`.** I named it as the one to tighten but did not edit it, since a tightening isn't one of the two kinds of change that count.
- **Pass and fail were scored by a script I wrote,** using the rules under Run Log — Before.

**The agent**
- **The diagnostic searches in `_empty_message()` call `tools.search_listings` directly,** not through MCP, so the failure path uses a different route from the main search. I left them because routing them through MCP would add up to two server launches to a failed search.
- **`call_tool` starts and stops the server on every call,** which adds latency. I haven't measured it.
- **`trace.step()` prints as it records,** so a run without `--trace` still shows the step lines. I left `trace.py` alone.
- **With an empty wardrobe, the agent gives generic advice and doesn't say so.** It passes criterion 4, but the user isn't told that nothing was drawn from their wardrobe.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
