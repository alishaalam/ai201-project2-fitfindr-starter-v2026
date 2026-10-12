# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries. Per
`run_eval.py`, this is one fixed query run 5 times with caching off, not 5
different queries.

**Why this target:** `search_listings` is deterministic — the same query
returns the same result every time, so across 5 identical tries it either
finds a match on all 5 or none; it can't produce a partial split by itself.
The real source of variance is downstream: `suggest_outfit` and
`create_fit_card` call the model with caching off, and `agent.py` doesn't yet
catch `ModelUnavailable` (still a Unit 4 TODO) — a transient API failure on
any one of the 5 tries would crash the run instead of completing. 4/5
acknowledges that risk; 5/5 would mean claiming the model call never fails
once across 5 tries, which isn't guaranteed.


---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:** `search_listings` guarantees an empty list — never
`None`, never an exception — when nothing matches (see Tool Inventory). The
branch in `run_agent` only has to check one fixed, guaranteed shape: is this
list empty. That's not a judgment call or a fuzzy outcome — it's a direct
check against a contract the tool itself enforces, so there's no scenario
where the branch should ever get it wrong.


---

## 3. The selected item never changes identity mid-pipeline

Given any run that reaches `suggest_outfit`, the `id` of `session["selected_item"]`
matches the `id` of the dict actually received as `suggest_outfit`'s `new_item`
argument, and that same `id` matches what `create_fit_card` receives as its
`new_item` argument too — verified against `trace.step()` logs — in 5 of 5
tries.

**Why this target:** This isn't a search-quality question or a model-output
question — it's "did `agent.py` pass the same dict through two more function
calls without it getting swapped or dropped." That's plain data-passing code
with no external dependency, so there's no scenario where it should be allowed
to miss. A failure here would be a wiring bug in `run_agent`, not a known
limitation of any tool, the same reasoning that makes criterion 2 a 5/5.


> **Revised in unit 4:** For every run that reaches `suggest_outfit`, the full dict received by `suggest_outfit` and by `create_fit_card` equals `search_results[0]` field for field, captured from the tool calls rather than read from the session, in 5 of 5 tries.
>
> **Why revised:** The original measured the wrong thing. It checked ids in the trace, but the trace is written from the same session variable that gets passed on, so a swapped or altered item would still have shown the same id. It also compared only the `id`, not the item. The new version is something that can actually fail. It has not been re-measured yet.
---

## 4. The empty-wardrobe path never falls back to nothing

Given a query run through the full agent loop with an empty wardrobe
(`wardrobe['items'] == []`), `suggest_outfit` returns a non-empty string of
general styling advice — never `""`, never a crash — in 5 of 5 tries. Per
`run_eval.py`, this is one fixed query run 5 times, not 5 different items.

**Why this target:** Recognizing an empty wardrobe is a deterministic branch
inside `suggest_outfit`, the same shape as criterion 2's check, so across 5
identical tries it takes the general-advice path every time — that part can't
vary. The only thing that could vary between tries is the model call itself:
an unhandled model-call failure (`ModelUnavailable`, which `agent.py` doesn't
catch yet) would crash one try while the others complete normally. I picked
this over the price-ceiling or speed options because the empty-wardrobe path
is otherwise untested by the other three criteria, and I'd rather find out now
whether it actually holds than discover it during grading.




---

## 5. A query with filters but no item word says no item was given

Given a query that has a size or price but no item word (e.g. `size M under
$50`), the agent stops before calling `suggest_outfit` and returns a message
saying it didn't get an item to search for — not a message claiming nothing
matched — in 5 of 5 tries.

**Why this target:** With no keywords, `search_listings` returns `[]`
regardless of size or price (see Tool Inventory), so the branch in `run_agent`
always takes the stop path, and `_empty_message` checks for the empty
description before it looks at any filter. No model is involved, so nothing can
vary between tries. It earns its own criterion because the message used to be
wrong: it printed `Nothing matched ""` and said no listing contains those
words, which was false since no keyword had been searched.


---

## 6. The item word outranks a colour in the search

> **Added in unit 4, after the Milestone 4 diagnosis.** The first five criteria
> all passed and none of them could see a search-ranking failure, so I added this
> one to measure it. It is written after the failure was found, which is the
> opposite of how the first five were written, so read it as a measurement of
> one known bug and not as an independent target.

Given a query with a colour and an item word where the catalog has that item
(`black sneakers under $60`), the title of `session["selected_item"]` contains
the item word — 5 of 5 tries.

**Why this target:** `search_listings` is deterministic and has no model in it,
so the same query returns the same ranking every time and the 5 tries can't
split. Before the fix every matched word counted 1, so `black` (in many
listings) tied with `sneakers` (in 2) and the tie fell back to file order,
putting an Oversized Flannel Shirt first. A check on one deterministic query is
either 5 of 5 or 0 of 5, so 5 of 5 is the only honest target.

---

## 7. The fit card always names the real price and platform

> **Restored in unit 4.** This was criterion 4 in unit 3. I removed it when I
> renumbered, then restored it, because the unit says never to delete an
> original. It is numbered 7 so the run-log rows for criteria 4–6 keep their
> numbers. The original text is below, unchanged, with the revision under it.

Given 5 fit cards generated for 5 different items, each card contains the
item's price as a literal `$` dollar figure and its platform name, each
exactly once as a substring — in at least 4 of 5 tries.

**Why this target:** `create_fit_card` calls a model, so the wording will
differ every time by design (see `config.TEMPERATURE`) — that's not what this
criterion checks. It checks two specific facts the prompt is supposed to force
into the output every time: the price and the platform, both pulled straight
from `new_item`, not invented by the model. Whether those facts show up is a
test of whether the prompt reliably constrains the model's formatting, and
models don't follow formatting instructions with perfect consistency — so 4/5
leaves room for an occasional drop without treating a single miss as proof the
tool is broken, the same shape of reasoning as criterion 1. Every listing in
`data/listings.json` has a non-null `price` and `platform` (checked all 40),
so the model always has both facts available going in — a miss here is never
a missing-data edge case, it's unambiguously the model dropping or
reformatting a fact it was given.

> **Revised in unit 4:** Given one item, `create_fit_card` is run 5 times with
> caching off, and each fit card contains the item's price as a literal `$`
> dollar figure and its platform name, each exactly once as a substring — in at
> least 4 of 5 tries.
>
> **Why revised:** The original said both "5 fit cards for 5 different items"
> and "4 of 5 tries", which are two different things to count, so it could not
> be scored as written. The revision uses one item run 5 times, the same shape
> as criteria 1–4. The target stays 4 of 5; it is not lowered.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
