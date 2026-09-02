# Country Explorer

A command-line tool for exploring live country data from the World Bank API —
search by name, rank a region by population, compare two countries, or export
a cleaned dataset to CSV.

Final project for **Python Intro 26.3 — Pilot** (Code the Dream), covering
Assignment 10 (Part I) and Assignment 11 (Part II).

## Submission links

| Field | Link |
|---|---|
| **Pull request** | https://github.com/ba-00001/python-intro-final-project/pull/1 |
| **Video — Part I (3–5 min)** | `VIDEO_URL_HERE` |
| **Video demo — Part II (2–4 min)** | `VIDEO_URL_HERE` |
| **Extension track** | **Option B — Data Cleaning & CSV Export** |
| **Mindset — Week 10** | [Information Literacy](#mindset-response--information-literacy-week-10) |
| **Mindset — Week 11** | [Self-Motivation](#mindset-response--self-motivation-week-11) |

## API

This project uses the [World Bank Indicators API](https://api.worldbank.org/v2/),
which is public, keyless and needs no registration. It reads two endpoints:

| Endpoint | Provides |
|---|---|
| `/v2/country` | name, `capitalCity`, `region.value`, `incomeLevel.value` |
| `/v2/country/all/indicator/SP.POP.TOTL` (`mrnev=1`) | most recent population per country |

### Why not REST Countries?

The course material recommends `restcountries.com`. **That API was deprecated
during the course** — it now answers with HTTP `200` and an error body rather
than country data:

```json
{"success": false, "data": null,
 "errors": [{"message": "This API version has been deprecated..."}]}
```

Its v5 replacement requires an API key (`Authorization: Bearer YOUR_KEY`), so
it is no longer a keyless public API. The World Bank API carries the same
fields and needs no key.

That substitution turned out to be the most useful thing that happened to this
project. A deprecated endpoint returning **200 with no data in it** is the
cleanest possible argument for why checking `status_code` alone isn't enough,
and it's the reason `fetch_data()` validates the response *shape* too.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/ba-00001/python-intro-final-project.git
   cd python-intro-final-project
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # macOS/Linux
   # .venv\Scripts\activate       # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python main.py
```

The program fetches both endpoints on startup, joins them, and reports how many
countries it loaded. It then shows a menu that repeats until you choose Quit:

```
Fetching country data from the World Bank API...
Loaded 217 countries.

=== Country Explorer ===
1. Search by name
2. Filter by region (sorted by population)
3. Compare two countries
4. Export cleaned data to CSV
5. Quit
Choose an option (1-5):
```

## CLI Interactions

- **Search by name** (option 1) — case-insensitive *partial* match, so `land`
  finds Finland, Iceland, Ireland, Poland, Switzerland and Thailand.
- **Filter by region** (option 2) — partial region match sorted by population,
  largest first. Typing `europe` matches `Europe & Central Asia` without having
  to know the World Bank's full region name.
- **Compare two countries** (option 3) — prints both and states which is larger
  and by how many people. An exact name match beats a partial one; a term that
  is still ambiguous lists the candidates rather than silently picking one.
- **Export cleaned data to CSV** (option 4) — the Week 11 extension. Writes a
  dated CSV and reports how many records were written and how many dropped.

Unexpected input never crashes the program: menu choices are compared as
strings, empty searches are rejected with a prompt, and an unrecognised choice
re-shows the menu.

### Examples

```
Choose an option (1-5): 2
Region: north america
  United States — Capital: Washington D.C. | Region: North America | Population: 341,784,857
  Canada — Capital: Ottawa | Region: North America | Population: 41,651,653
  Bermuda — Capital: Hamilton | Region: North America | Population: 64,555
  (3 results)

Choose an option (1-5): 3
First country: France
Second country: Germany

  France — Capital: Paris | Region: Europe & Central Asia | Population: 68,720,337
  Germany — Capital: Berlin | Region: Europe & Central Asia | Population: 83,491,249

  Germany is larger by 14,770,912 people.

Choose an option (1-5): 3
First country: land
Second country: Chad
'land' is ambiguous — did you mean: Switzerland, Channel Islands, Cayman Islands, Finland, Faroe Islands?

Choose an option (1-5): 4
Wrote 217 rows to ./countries_clean_2026-09-02.csv
Dropped 0 records that failed cleaning.
```

## Files

| File | What it does |
|---|---|
| [main.py](main.py) | Entry point — fetching, parsing, and the CLI |
| [export.py](export.py) | Week 11 extension — cleaning and CSV export |
| [countries_clean_2026-09-02.csv](countries_clean_2026-09-02.csv) | Sample export output |
| [requirements.txt](requirements.txt) | `requests` and its dependencies |

`.venv/` is gitignored.

### Code organisation

Fetching, parsing, display and export are separate:

| Function | Responsibility |
|---|---|
| `fetch_data(path, params)` | One HTTP GET. Returns rows or `None`. Knows nothing about countries. |
| `fetch_populations()` | The population endpoint → `{ISO3: population}` |
| `process_data(rows, populations)` | Raw API rows → clean list of dicts |
| `load_countries()` | Orchestrates the two fetches and the join |
| `search_by_name` / `filter_by_region` / `compare_countries` | The three interactions |
| `format_country` / `display_results` | Presentation only |
| `export.clean_country` / `clean_countries` | The cleaning framework |
| `export.write_csv` / `export_countries` | `csv.DictWriter` output |

`fetch_data` takes the path and query parameters as **arguments** rather than
hard-coding a URL, which is what lets one function serve both endpoints and
guarantees `format=json` is never omitted.

## Standard library modules used

Beyond `csv`: **`os.path`** (`os.path.join` for the output path, so the
separator is right on any platform) and **`datetime`** (a dated output
filename, so re-running the export doesn't silently overwrite the previous
file).

## Data Cleaning Decisions

The export applies a **per-field decision framework**. For each field I decided
in advance what a missing or malformed value means — and crucially, that the
answer differs by field. The three possible answers are not interchangeable.

| Field | Missing / invalid looks like | Decision |
|---|---|---|
| `name` | empty string, or key absent | **DROP the record** |
| `region` | empty, or the string `Aggregates` | **DROP the record** |
| `population` | `0`, `None`, non-numeric, negative | **DROP the record** |
| `capital` | `""` or the sentinel `"N/A"` | **KEEP**, write `""` |
| `income_level` | `""` or absent | **KEEP**, write `Not classified` |

### Which fields I included, and why

`name`, `capital`, `region`, `income_level`, `population`, and a derived
`population_millions`.

The reasoning for the split is that **the three DROP fields are what the export
exists to carry.** A row with no name can't be identified, a row with no region
can't be grouped, and a row with no population can't be ranked or summed — the
three things a consumer of this file would actually do with it. A record missing
any of them isn't incomplete data, it's not a record.

`capital` and `income_level` are descriptive. Their absence is a genuine fact
about the place — Hong Kong SAR has no capital in this dataset because it isn't
a sovereign state — not a broken row. Dropping those six countries to keep the
column tidy would be discarding correct data to make the file look neater,
which is the wrong trade.

### What I did with missing and invalid values

**`capital`: sentinel → real blank.** The API sends the literal string `N/A`.
That's fine on screen but wrong in a data file, because a consumer can't tell
it from a country genuinely named that. It's converted to an empty CSV field,
which is what "unknown" means in a CSV. Six rows are affected.

**`income_level`: blank → explicit label.** The opposite decision, on purpose.
Here the World Bank's own vocabulary has a term for it — `Not classified` — so
writing that is more informative than a blank, and it keeps the column
categorical rather than mixing categories with holes.

**`population`: zero is not a number.** The fetch step uses `0` as a
placeholder so sorting never has to special-case `None`. The export treats `0`,
negatives and non-numerics identically: no usable figure, drop the record. This
is the one that would bite hardest if left in — a `0` silently included in an
average or a total corrupts the answer without any error.

**Whitespace everywhere.** Every text field is `.strip()`ed. The World Bank
returns region values with a trailing space (`"Sub-Saharan Africa "`), which
would otherwise produce two distinct groups when anyone grouped by region.

### Type coercion applied

- `population` → `int`, via `int(str(raw).strip())`. The API already sends an
  int, but an export shouldn't trust the upstream type; this normalises a
  string, an int and a float identically. `TypeError` and `ValueError` are both
  caught, since `None` raises the former and `"abc"` the latter.
- `population_millions` → `float` rounded to 2dp. Added **alongside** the exact
  figure, not instead of it — rounding is a convenience for the reader, and
  discarding precision in an export can't be undone downstream.
- All text fields → `str`, stripped.

### Ordering and reporting

Rows are sorted by population descending, so the file has a deliberate order
rather than whatever sequence the API returned. The CLI reports both counts:

```
Wrote 217 rows to ./countries_clean_2026-09-02.csv
Dropped 0 records that failed cleaning.
```

Reporting the dropped count matters as much as the written one. A silent export
looks identical whether it discarded nothing or half the dataset, and "my
cleaning script quietly ate 40% of the rows" is exactly the failure this course
has taught me to make visible. On the current live data nothing is dropped —
every one of the 217 countries has a usable name, region and population — but
the framework is verified against malformed input rather than assumed to work.

## Verified cleaning behaviour

Each branch was checked directly against malformed records:

| Input | Result |
|---|---|
| valid record | kept |
| `name` empty / key absent | DROPPED |
| `region` = `Aggregates` / empty | DROPPED |
| `population` = `0` / `None` / `"not_a_number"` / `-5` | DROPPED |
| `population` = `"  2500  "` | kept, coerced to `2500` |
| `capital` = `"N/A"` | kept, written as `""` |
| `income_level` absent | kept, written as `Not classified` |

## Mindset Response — Information Literacy (Week 10)

> *"Without data, you're just another person with an opinion."*
> — W. Edwards Deming

### 1. When was a time you got wrong information or an artificial intelligence tool has given you bad/weird answers? Share about that experience here.

The one I keep coming back to is being handed a function that didn't exist. I
asked an AI assistant how to do something, got back a tidy few lines calling a
method on a library I was using, and it looked exactly like every other correct
answer I'd been given. It wasn't a real method. Nothing in the tone, the
formatting or the confidence distinguished it from the truth. I lost a while
assuming I'd installed the wrong version.

This project produced a better example, though, and it wasn't AI's fault. The
course material — the authoritative source, the thing I'm supposed to trust —
told me to use `restcountries.com/v3.1`. That was correct when it was written
and it is wrong now. The API returns HTTP `200`, which every check I'd have
thought to write says means success, and the body is a deprecation notice. My
first version of the code "worked", took the 200 as a green light, and produced
zero countries with no error at all.

Then I made it worse myself: I joined the two endpoints on the wrong `id`
field, and because I'd used `.get(key, 0)` to be defensive, every population
came out as `0` instead of raising. Two silent failures stacked on top of each
other, both introduced by me being careful in the wrong way. Nothing in this
project taught me more than that.

### 2. What are some 'clues' that you use to help you assess whether a resource or AI is accurate/trustworthy/up-to-date or not?

**Can I run it?** This is the only one that really settles anything. Everything
else is a prior. `curl` the endpoint, print the response, look at what actually
came back. I found the deprecation because I printed the raw JSON before
writing the parser, not because I doubted the assignment.

**Is it first-hand?** The World Bank's own documentation beats a blog post
about it. I've stopped landing on search results for `csv.DictReader` and go to
the standard library docs — they're correct, they're for the version I'm
running, and they're not older than the feature.

**Does it name a version?** Advice without a version attached is a guess about
which version you're on. Half the wrong answers I've been given were right two
releases ago.

**Is it too fluent for how obscure it is?** The specific failure mode of AI
answers is that confidence doesn't drop when accuracy does. So an extremely
smooth answer about something niche now raises my suspicion rather than
lowering it. A human expert usually hedges; a hallucination doesn't.

**Does the shape match, not just the status?** This is the new one, and it's
this project's contribution. A `200` told me the request succeeded, and I'd been
treating that as "the data is good". It means the server answered. Those are
different claims, and I now check both — `fetch_data()` validates the response
structure as well as the status code, because the thing that lied to me wasn't
an AI or a blog post. It was the assignment, and the API agreed with it.

## Mindset Response — Self-Motivation (Week 11)

> *"The only way to do great work is to love what you do."* — Steve Jobs

### 1. Time to look back and look forward: When you started this particular class we asked you why you wanted to be a software developer and what you wanted to do with your skills after the class ends. Have your answers changed? What are your answers now?

In Week 3 I said I wanted to stop building things by copying examples, because
my side projects worked right up until they didn't and then I was stranded. I'd
give the same answer now, but I understand what I was asking for better than I
did.

What's changed is that I thought the missing thing was knowledge — enough
Python that I'd stop being stuck. It isn't. It's a process for when I *am*
stuck, which is a permanent condition rather than a phase. This project is the
proof: I hit a deprecated API and a silent join bug, and neither was solved by
knowing more Python. They were solved by printing the raw response before
trusting it, and by comparing two key sets side by side instead of guessing.
Eleven weeks ago I'd have thrashed at both for a day. That shift matters more
than any syntax I've picked up.

The other change is that the boring parts stopped feeling boring. I wrote in
Week 4 that branch-per-assignment felt like performing a ritual I didn't
understand. I still haven't had the disaster it protects against — but I've now
had the Week 6 refactor, where having the Week 5 version intact in the history
meant I could rewrite the whole thing without any anxiety about it. That's the
first time version control did something *for* me rather than to me.

What I want to do after hasn't changed: finish one of my own projects properly
instead of abandoning it at 80%, and work toward doing this for a living. What's
different is that I'd now define "properly" as documented, error-handled, and
comprehensible to someone who isn't me — which is not what I would have meant
in June.

I'd also be honest that my worst weeks here had nothing to do with difficulty.
Weeks 2 and 3 went in late because I went quiet when I fell behind, and the
Week 2 confusion cost days over a question that would have taken a minute to
ask. That's the habit I most want to have broken, and I don't think it's fixed
yet — just visible.

### 2. What is your plan for the next 3 months / year / 5 years?

**Next 3 months.** Finish the language-learning project to an actual release
rather than a working state on my machine — which means the accessibility work
I identified in Week 9 (transcripts for every audio clip, adjustable timings),
a README someone else could follow, and error handling on anything that touches
the network. I want to apply this course's habits to code that predates them.
Also: keep writing something small every week, because eleven weeks of steady
practice did more than any single project has, and I know from Weeks 2 and 3
that catching up costs more than keeping up.

**Next year.** Get properly comfortable with the things this course deliberately
left out — testing beyond running the file and reading the output, working in
someone else's codebase, and Git under real conditions rather than one person
on one branch. Git has been the hardest part of this course for me by a wide
margin, and I want the screen-share sessions I proposed in Week 6: deliberately
break things in a throwaway repo with someone who's already hit those problems.
Continue into the Python for Data Analysis track. Build something with another
person, because everything I've made so far has been alone, and collaboration
is the skill I have least evidence of.

**Next 5 years.** Working as a developer, and specific about the shape rather
than the title: somewhere I'm the least experienced person in the room for a
while, because that's the fastest way to learn and I've spent enough time being
the only person looking at my own code. Data and automation is where my
curiosity keeps leading, so probably that direction.

Five years is far enough out that a detailed plan would be fiction, and the last
eleven weeks have made me suspicious of plans that don't survive contact with
reality. So the real answer is a direction and a rate: keep shipping things I
could explain line by line, keep asking earlier than is comfortable, and stay
in rooms where I'm not the most capable person. That compounds. The specific
job title at the end of it, I don't need to know yet.
