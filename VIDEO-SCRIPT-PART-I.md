# Final Project Part I (Assignment 10) — Video Reflection Script

**Target length:** 3–5 minutes (this script runs ~4:35 spoken at a normal pace).
**Track:** Week 10 core program. The Week 11 extension has its own script:
[VIDEO-SCRIPT-PART-II.md](VIDEO-SCRIPT-PART-II.md).

**What the lesson explicitly asks this video to cover**

1. Walk through `fetch_data()`. What does it do if the API call fails?
2. Demonstrate the CLI live with at least one real input. What happens on
   unexpected input?
3. Walk through one decision about how you organised the code into functions,
   and explain why.

Everything below is built around those three, in that order, because that's the
order the reviewer will be marking against.

**Before you hit record**

- Terminal cleared, in the project root, venv active (`(.venv)` in the prompt).
- **Live internet required.** Run `python main.py` once first to confirm the
  World Bank API is answering and that it loads 217 countries.
- Editor tabs: `main.py` (scrolled to `fetch_data`) and `requirements.txt`.
- Browser tab on `https://api.worldbank.org/v2/country?format=json&per_page=5`
  so you can show the `[metadata, [rows]]` wrapper rather than describe it.
- Planned live inputs, in this order:
  - **1** → `land` (partial match: Finland, Iceland, Ireland, Poland,
    Switzerland, Thailand)
  - **2** → `north america`
  - **3** → `France` then `Germany`
  - **3** again → `land` then `Chad` (shows the ambiguity guard)
  - **9** (unexpected input — the menu just re-shows)
  - **5** to quit
- Do **not** demo option 4 here. That's the Week 11 extension and it belongs in
  the Part II video.

---

## 0:00 – 0:30 · Intro (webcam)

> Hey, I'm Brian Bazurto, and this is Part One of my final project for Python
> Intro 26.3 with Code the Dream. The project is called **Country Explorer** — a
> command-line tool over live country data, where you can search by name, rank a
> region by population, or compare two countries.
>
> Before the code, one thing about the API, because it's the reason the project
> looks the way it does.

*(Switch to screen share.)*

---

## 0:30 – 1:00 · Which API, and why not the one in the brief

> The project overview suggests `restcountries.com`. **That API was deprecated
> during this course.** It now answers with HTTP **200** and an error body where
> the country data used to be, and its v5 replacement requires an API key — so
> it's not a keyless public API any more.
>
> I switched to the **World Bank Indicators API**. Keyless, no registration, and
> it carries everything I need: name, capital, region, income level and
> population.

*(Show the browser tab with the raw JSON.)*

> One thing about its shape, because it drives the code: the World Bank wraps
> every response as a two-item list — `[0]` is pagination metadata, `[1]` is the
> actual rows. And the fields I want live in **two different endpoints**, so the
> program fetches both and joins them.

---

## 1:00 – 2:00 · `fetch_data()` — and what it does when the call fails

*(Open `main.py`, scroll to `fetch_data`.)*

> This is `fetch_data`, and it's the function the assignment asks me to walk
> through. It does exactly one thing: one HTTP GET. It knows nothing about
> countries — you give it a path and some query parameters and it hands back rows.

*(Highlight the `query = dict(DEFAULT_PARAMS)` merge.)*

> The parameters are **merged over** defaults rather than replacing them, so a
> caller can't forget `format=json` — and the World Bank answers in XML if you
> omit it. Passing the path and params as **arguments**, instead of baking a URL
> into the function, is what lets this one function serve both endpoints.
>
> Now — what happens when the call fails. There are **three** distinct failures
> here, and they're deliberately separate.

*(Highlight the `except requests.exceptions.RequestException`.)*

> **One — it never reached the server.** DNS failure, no connection, timeout.
> `RequestException` is the base class of requests' own errors, so one clause
> covers all of them, and that's right because the user's next step is the same
> for every one: check your connection. It prints a message and returns `None`.

*(Highlight the status check.)*

> **Two — it reached the server, but the status isn't 200.** A response arriving
> is not the same as a response being useful.

*(Highlight the `isinstance` shape check.)*

> **Three — a 200 whose shape is wrong.** And this check exists *because* of the
> deprecated API. It returned a perfectly healthy 200 with a deprecation notice
> where my data should have been. If I'd only checked the status, I'd have gone
> straight on to index into something that wasn't a list of rows and crashed with
> an `IndexError` or a `KeyError` somewhere far away from the actual problem.
>
> So it returns `None` in all three cases, never a half-built result. And every
> caller checks for `None` and stops. `load_countries` returns `None`, and `main`
> prints "cannot continue without data" and exits — instead of showing an empty
> menu over no data.

*(Highlight `timeout=30`.)*

> And the timeout, because without it a server that accepts the connection and
> then never replies just hangs the program, with nothing to catch.

---

## 2:00 – 3:00 · The CLI, live (screen: terminal)

```bash
python main.py
```

> It fetches both endpoints, joins them, and tells me how many countries it
> loaded — 217, after filtering out the World Bank's aggregate rows like "Arab
> World" and "Euro area", which aren't countries.

*(Option 1, search `land`.)*

> Search is a **substring** match, so `land` finds Finland, Iceland, Ireland,
> Poland, Switzerland and Thailand. That's deliberate — I don't want to have to
> type a country's exact name to find it.

*(Option 2, region `north america`.)*

> Region filter is partial too, and sorted by population, largest first. So I can
> type `europe` and match "Europe & Central Asia" without knowing the World Bank's
> exact region name.

*(Option 3, France then Germany.)*

> Compare prints both and then states which is larger and by how many people —
> stated explicitly rather than leaving you to work it out from a sign.

*(Option 3 again, `land` then `Chad`.)*

> And here's the interesting case. `land` matches six countries, so rather than
> silently picking one, it tells me it's ambiguous and lists the candidates. An
> **exact** name match still wins over a partial one, though — which is why
> typing `Chad` gets Chad and isn't confused by a longer name containing it.

*(Type `9` at the menu.)*

> Unexpected input: the menu just re-shows. That's because the choice is compared
> as a **string** — there's no `int()` on it — so typing letters, or hitting enter
> on an empty line, falls through to the `else` instead of crashing. Same for the
> searches: an empty search term gets a prompt rather than returning all 217
> countries.

*(Quit with 5.)*

---

## 3:00 – 4:05 · One organisation decision, and why

*(Back to `main.py`, scroll so `fetch_data`, `fetch_populations`, `process_data`
and `load_countries` are all visible.)*

> The decision I want to explain is the split between these four functions,
> because the obvious version of this program is one function that fetches and
> parses in a single pass.
>
> `fetch_data` does one HTTP GET and knows nothing about countries.
> `fetch_populations` knows about the population endpoint. `process_data` does no
> networking at all — you hand it rows and it hands back clean dictionaries.
> `load_countries` is the only one that knows the *whole* story.
>
> Two reasons this shape earned itself.

*(Highlight `fetch_populations` and the `countryiso3code` comment.)*

> First — the bug it made findable. Both endpoints have a field called `id`, and
> they hold **different identifiers**. The population rows put a World Bank code
> like `"ZH"` or `"1A"` in `country.id`, and keep the ISO3 code in
> `countryiso3code`. I joined on the wrong one, and it matched **nothing** — every
> population came back as zero. Silently, because `.get(key, 0)` did exactly what
> I told it to.
>
> No error, 217 countries loaded, every population zero. And because the join was
> in `fetch_populations` on its own, I could look at that one function's output in
> isolation and see immediately that the keys were wrong. If fetching and joining
> had been one blob I'd have been guessing which half was broken.
>
> Second — `process_data` takes rows and populations as **arguments** and returns
> a list. It never touches the network, which means I can reason about the
> transformation without an internet connection being part of the question.
>
> And the same principle runs down to the small functions: `search_by_name` and
> `filter_by_region` **return** lists, and `display_results` is the only thing
> that prints. Search answers "which ones match"; display decides what that looks
> like. That's why the export feature in Week 11 could reuse the same country
> list without a single print statement getting in the way.

---

## 4:05 – 4:35 · Close (webcam)

> So that's Part One: `requests` against a live API, the response parsed into a
> list of dictionaries, three separate failure modes handled, and a CLI with four
> interactions that doesn't crash on anything I've thrown at it.
>
> The thing I'd underline is that the deprecated API made this project better. An
> endpoint that returns 200 with no data in it is the cleanest possible argument
> for why checking the status code isn't enough — and my `fetch_data` validates
> the shape because of it.
>
> Part Two adds the data cleaning and CSV export. Everything's in the pull request
> and the README. Thanks for watching.

---

## Delivery notes

- Hit the three required beats in order — `fetch_data` failure handling, live CLI
  with unexpected input, one organisation decision. A reviewer is ticking those.
- Show the ambiguity case (`land` vs `Chad`). It's the most interesting thing the
  CLI does and it takes fifteen seconds.
- **Don't demo option 4.** Save the CSV export for the Part II video.
- Check the API is up immediately before recording. If it's down, say so on camera
  and walk the code — don't fake output.
- Under 3:00 reads as thin; over 5:00 gets cut off. Time your first take.

---

## Video URL

Upload to YouTube (unlisted) or Loom, then paste the link here and in the places
below. Lesson 10 requires the link **in the pull request description**.

**Video URL:** `VIDEO_URL_HERE`

| Also paste it into | Where |
| --- | --- |
| Pull request description (required) | [python-intro-final-project#1](https://github.com/ba-00001/python-intro-final-project/pull/1) |
| README submission table, "Video — Part I" row | [README.md](README.md) |
| Course index video table, row 10 | [main README](https://github.com/ba-00001/brian-bazurto-python/blob/main/README.md#video-reflections) |
