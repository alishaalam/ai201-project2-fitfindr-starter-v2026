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

- **What it does:** Searches the listings dataset for items matching a text description, with optional size and max-price filters, and returns the best matches ranked by keyword overlap.
- **Inputs:** `description` (str) — keywords describing what the user wants, e.g. `"vintage graphic tee"`. `size` (str | None, default `None`) — a size to filter by; `None` skips size filtering. Match rule: normalize both the requested size and each listing's size (lowercase, strip whitespace, drop any parenthetical like `"(fits oversized)"`), then match if they're equal OR both appear together in a small fixed alias table (e.g. `"m"` aliases to `"s/m"` and `"m/l"`, `"oversized"`/`"baggy"` alias to `"xl"`, `"petite"`/`"tiny"` alias to `"s"`) — no substring matching, so `"l"` never matches `"xl"`. Shoe sizes (`US 7`–`US 9`) and waist sizes (`W27`–`W32`, `W30 L30`) match only on exact equality after normalization, with no aliasing to the letter scale. A size term with no entry in the alias table (e.g. a relative description like `"big feet"`) is not parsed into `size` at all — it stays in `description`, where it only affects keyword-overlap ranking, not filtering. `max_price` (float | None, default `None`) — maximum price, inclusive; `None` skips price filtering.
- **Returns:** A `list[dict]` of matching listings, best match first. Each dict has `id, title, description, category, style_tags (list[str]), size, condition, price (float), colors (list[str]), brand (str or None), platform`.
- **When it has nothing:** An empty list — not `None`, and not an exception.

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
  stopped: Nothing in the listings matched "designer ballgown", under $5, size XXS. Try to raise your max price; drop the size or try a neighbouring one (e.g. M also matches S/M and M/L); use fewer or more general keywords (e.g. 'tee' instead of a brand or colour).
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
- *What I changed:* The loop itself I kept as written. I then asked Claude to read the empty-search message cold, as a user who knows nothing about the app. Its verdict: the message names three levers but doesn't say which one caused the miss; "neighbouring size" and the "M also matches S/M" example don't help for `XXS`; and "fewer or more general keywords" pulls in two directions. I recorded that as a known weakness (see Open Questions below) instead of rewriting the message, because the assignment says to work out the fix myself and the honest finding is that the message is not finished.

**Everything else AI did in this project**

| Milestone | What Claude did | Result |
|---|---|---|
| 2 | Helped draft the three tool specs and the loop branch rule | `a37431a`, then the size gap fixed in `84fca98` |
| 3 | Helped write the five acceptance criteria with targets and reasoning | `3b01e7c`, `criteria.md` |
| 4 | Implemented `search_listings`, `suggest_outfit`, `create_fit_card` in `tools.py` | `6efacd8`; per-tool tests below |
| 5 | Implemented `run_agent`, `_parse_query`, `_empty_message` | `58a1a94` |
| 6 | Filled in this README from verified output (nothing pasted that wasn't run) | this commit |

**Open Questions (empty-search message)**

- The message lists every applied filter but not which one blocked the search. Fixing that means re-searching with each filter dropped in turn, which adds tool calls.
- It doesn't say what the catalog contains, so a user who typed "ballgown" can't know to try "dress".

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

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
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



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
