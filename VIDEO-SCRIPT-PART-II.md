# Final Project Part II (Assignment 11) — Video Demo Script

**Target length:** 2–4 minutes — shorter than every other video in this course.
This script runs ~3:20 spoken at a normal pace. Do not let it drift past 4:00.
**Track:** **Option B — Data Cleaning & CSV Export.**
Part I has its own script: [VIDEO-SCRIPT-PART-I.md](VIDEO-SCRIPT-PART-I.md).

**What the lesson explicitly asks this video to cover**

1. Run the complete project from `main.py` entry to output — show it working live.
2. Show the extension deliverable (the CSV) and explain **one decision** you made
   while building it.
3. If you had more time, what would you add or improve?

Three beats, and the time limit is tight, so this script is deliberately lean.

**Before you hit record**

- Terminal cleared, project root, venv active (`(.venv)` visible).
- **Live internet required.** Run it once beforehand to confirm the API answers.
- **Delete today's export file** so you write it live:
  `rm countries_clean_$(date +%F).csv` — the committed sample from 2026-09-02 stays.
- Editor tabs: `export.py` (scrolled to the module docstring, which holds the
  decision table) and `main.py`.
- Have a spreadsheet app or `column -s, -t` ready to open the CSV nicely:
  `column -s, -t < countries_clean_$(date +%F).csv | head -15`
- Planned run: option **1** search `Japan` (quick proof the Week 10 program still
  works), then option **4** to export, then **5**.

---

## 0:00 – 0:20 · Intro (webcam)

> Hey, I'm Brian Bazurto, and this is Part Two of my final project for Python
> Intro 26.3 with Code the Dream. Part One built **Country Explorer**, a CLI over
> live World Bank country data. For Week 11 I took **Option B — data cleaning and
> CSV export**. Let me run the whole thing.

*(Switch to screen share, terminal.)*

---

## 0:20 – 1:05 · The complete project, end to end (screen: terminal)

```bash
python main.py
```

> Entry point is `main.py`. It fetches both World Bank endpoints, joins them, and
> loads 217 countries.

*(Option 1, search `Japan`.)*

> That's the Week 10 program, still doing what it did — search, region filter and
> comparison are all unchanged.

*(Option 4.)*

> And option 4 is the extension. It writes a dated CSV and reports **two** numbers:
> how many rows it wrote, and how many records it dropped.

*(Point at the "Dropped" line.)*

> That second number is there on purpose. A silent export looks identical whether
> it dropped nothing or half the dataset, and I'd rather know.

*(Quit with 5, then show the file.)*

```bash
column -s, -t < countries_clean_$(date +%F).csv | head -15
```

> There's the file — six columns, header row, sorted by population so the file has
> a meaningful order rather than whatever sequence the API happened to return.

---

## 1:05 – 2:20 · The decision: cleaning is per **field**, not per file

*(Open `export.py`, scroll to the decision table in the module docstring.)*

> Here's the decision I want to explain, and it's the one the whole extension
> turns on.
>
> When I started I assumed "cleaning the data" was one policy you apply to the
> file. It isn't. For every field you have to decide, in advance, what a missing
> or malformed value **means** — and there are three possible answers that are not
> interchangeable: substitute something, leave it blank, or throw the whole record
> away.

*(Point at the table, row by row.)*

> So: **name, region and population** — if any of those is missing or invalid, I
> **drop the record**. **Capital and income level** — I **keep** the record and
> record the gap honestly.
>
> The reasoning for that split is what the export is *for*. A row with no name
> can't be identified, a row with no region can't be grouped, and a row with no
> population can't be ranked or summed — those are the three things anyone using
> this file would actually do with it. A record missing any of them isn't
> incomplete data, it's **not a record**.
>
> But a country with no listed capital is a real fact about that country, not a
> broken row. Dropping it would be throwing away good data to satisfy a rule that
> was never about it.

*(Scroll to `clean_population`.)*

> Two details that fell out of that. `clean_population` treats **zero** as
> missing — because zero is the placeholder the fetch step uses for "no figure
> available", and a negative population is impossible, so both mean the same
> thing. And it converts with `int(str(...))` inside a `try`, because an export
> shouldn't assume the upstream type stays what it is today.

*(Scroll to the `UNKNOWN_CAPITAL` handling.)*

> And the API sends the literal string `"N/A"` where a capital is unknown. I treat
> that as a **sentinel** and write a genuine blank, so a reader can tell "unknown"
> from a country whose capital is actually spelled N/A. Income level goes the
> other way — an explicit `"Not classified"`, because there the label is the
> information.

*(Scroll to `write_csv`.)*

> The write itself is `csv.DictWriter` with the column order declared as a
> constant at the top, not derived from the dictionaries — dict order is an
> implementation detail, and a file's header should be a deliberate, stable
> contract. And `newline=""`, which is the documented setting for the csv module;
> without it, every row on Windows gets a blank line after it.
>
> Standard library beyond `csv`: **`datetime`** for the dated filename, so
> re-running the export doesn't silently overwrite yesterday's file, and
> **`os.path.join`** so the separator is right on any platform.

*(Briefly show the `from export import export_countries` line in `main.py`.)*

> And all of this lives in its own module. `main.py` imports one function.
> Cleaning and exporting is a different job from fetching and browsing, and
> keeping them apart meant the Week 10 code didn't have to change to gain a
> feature.

---

## 2:20 – 3:05 · With more time (webcam or screen)

> Three things I'd do with more time.
>
> **One — I'd write tests for the cleaning functions.** `clean_country` is pure:
> hand it a dict, get a dict or `None` back, no network, no files. That's the
> easiest thing in this whole project to test, and right now the only way I know
> it handles a negative population is that I typed one in by hand once.
>
> **Two — I'd let the export take a filter.** Right now option 4 exports
> everything. But `filter_by_region` already returns a list in exactly the shape
> `export_countries` accepts, so "export just Europe" is close to free — I'd be
> wiring two things I already have together rather than writing anything new.
>
> **Three — I'd cache the API response to disk.** Every run re-fetches both
> endpoints, which is slow and is 217 countries' worth of traffic for data that
> changes about once a year. And it would make the program usable offline, which
> matters more to me than it might sound like — I've spent a lot of time on
> connections that don't reliably answer.
>
> The one I'd actually do first is the tests, because it's the only one that would
> have caught a real bug I shipped in Week 10.

---

## 3:05 – 3:20 · Close (webcam)

> So that's the final project. Country Explorer, four CLI interactions over a live
> keyless API, extended with a per-field cleaning framework and a CSV export.
>
> The thing I'm taking out of it: "clean the data" isn't one decision. It's one
> decision per field, and you have to make them before you write the loop.
> Everything's in the pull request and the README. Thanks for watching, and thanks
> for the course.

---

## Delivery notes

- **Watch the clock.** This one is 2–4 minutes, not 3–5. If you're running long,
  cut the second and third "with more time" items and keep the tests one.
- Delete today's CSV before recording so it gets written on camera. Showing the
  file appear is worth more than pointing at a committed one.
- The per-field framework is the graded idea. "A record missing name, region or
  population isn't incomplete data, it's not a record" is the sentence to land.
- Don't re-explain `fetch_data` — that was the Part I video. Assume it.
- Check the API is up right before recording. If it's down, say so on camera and
  walk the code and the committed sample CSV instead of faking output.

---

## Video URL

Upload to YouTube (unlisted) or Loom, then paste the link here and in the places
below. Lesson 11 requires the link **in the pull request description AND in the
README** — that's two required locations, not one.

**Video URL:** `VIDEO_URL_HERE`

| Also paste it into | Where |
| --- | --- |
| Pull request description (required) | [python-intro-final-project#1](https://github.com/ba-00001/python-intro-final-project/pull/1) |
| README submission table, "Video demo — Part II" row (required) | [README.md](README.md) |
| Course index video table, row 11 | [main README](https://github.com/ba-00001/brian-bazurto-python/blob/main/README.md#video-reflections) |
