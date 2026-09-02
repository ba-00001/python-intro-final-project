"""Week 11 extension - clean the API data and export it to CSV.

Kept in its own module rather than added to main.py, because cleaning and
exporting is a separate job from fetching and browsing. main.py imports what
it needs from here.

The cleaning follows a per-field decision framework: for every field, decide
in advance whether a missing or malformed value means "substitute something",
"leave it blank" or "throw the whole record away". Those three answers are not
interchangeable, and picking per field rather than per file is the point.

    field         | missing / invalid          | decision
    --------------|----------------------------|------------------------------
    name          | empty or absent            | DROP the record
    region        | empty or "Aggregates"      | DROP the record
    population    | 0, None, non-numeric       | DROP the record
    capital       | "" or the sentinel "N/A"   | KEEP, write "" (unknown)
    income_level  | "" or "Not classified"     | KEEP, write "Not classified"

name, region and population are the fields the export exists to carry - a row
missing any of them is not a usable record, so it goes. capital and
income_level are descriptive: their absence is a real fact about the country,
not a broken row, so the record stays and the gap is recorded honestly.
"""

import csv
import os
from datetime import datetime

# Column order for the CSV. Declared here rather than derived from the dicts,
# because dict order is an implementation detail and the file's header should
# be a deliberate, stable contract.
FIELDNAMES = [
    "name",
    "capital",
    "region",
    "income_level",
    "population",
    "population_millions",
]

# The upstream API uses this string where a capital is unknown. Treating it as
# a sentinel rather than data keeps "unknown" out of the exported values.
UNKNOWN_CAPITAL = "N/A"


def clean_population(raw):
    """Return the population as a positive int, or None if unusable."""
    # The API sends this as an int already, but an export shouldn't assume the
    # upstream type. int(str(...)) normalises a str, an int and a float alike.
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        # Non-numeric, None, or empty. Either way there is no number here.
        return None

    # Zero is the placeholder the fetch step uses for "no figure available", and
    # a negative population is impossible - both mean the same thing to us.
    if value <= 0:
        return None

    return value


def clean_text(raw, default=""):
    """Return raw stripped of whitespace, or default if it's empty."""
    if raw is None:
        return default

    text = str(raw).strip()

    return text if text else default


def clean_country(country):
    """Return a cleaned export row, or None if the record is unusable.

    This is the per-field framework in code. The three DROP fields are checked
    first, so a doomed record costs no further work.
    """
    name = clean_text(country.get("name"))

    if not name:
        return None

    region = clean_text(country.get("region"))

    # "Aggregates" marks the World Bank's non-country rows (Euro area, Arab
    # World). main.py filters them already; repeating it here means this module
    # is safe to point at any list, not just one that's been pre-filtered.
    if not region or region == "Aggregates":
        return None

    population = clean_population(country.get("population"))

    if population is None:
        return None

    # KEEP fields. The sentinel becomes a genuine blank, so a reader can tell
    # "unknown" from a literal string that happens to say N/A.
    capital = clean_text(country.get("capital"))

    if capital == UNKNOWN_CAPITAL:
        capital = ""

    income_level = clean_text(country.get("income_level"), default="Not classified")

    return {
        "name": name,
        "capital": capital,
        "region": region,
        "income_level": income_level,
        "population": population,
        # A derived column, rounded for readability. Kept alongside the exact
        # figure rather than replacing it - rounding is for the reader, and
        # throwing away precision in an export is not recoverable.
        "population_millions": round(population / 1_000_000, 2),
    }


def clean_countries(countries):
    """Clean a list of countries. Returns (rows, dropped) where dropped is a count."""
    rows = []
    dropped = 0

    for country in countries:
        row = clean_country(country)

        if row is None:
            dropped += 1
            continue

        rows.append(row)

    # Sorted by population so the file has a meaningful order rather than
    # whatever sequence the API happened to return.
    rows.sort(key=lambda r: r["population"], reverse=True)

    return rows, dropped


def build_filename(directory="."):
    """Return a dated output path like ./countries_clean_2026-09-02.csv."""
    # datetime is the standard-library module used beyond csv. A dated filename
    # means re-running the export doesn't silently overwrite yesterday's file.
    stamp = datetime.now().strftime("%Y-%m-%d")

    # os.path.join rather than f"{directory}/..." so the separator is correct
    # on any platform.
    return os.path.join(directory, f"countries_clean_{stamp}.csv")


def write_csv(rows, path):
    """Write rows to path using csv.DictWriter. Returns the number written."""
    # newline="" is the documented setting for the csv module. Without it, on
    # Windows every row gets an extra blank line between it and the next.
    with open(path, "w", newline="") as f:
        # DictWriter maps each dict to columns by key, so the header and the
        # row order can never drift apart the way they can with a plain writer
        # and hand-built lists.
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def export_countries(countries, directory="."):
    """Clean and export in one call. Returns (path, written, dropped)."""
    rows, dropped = clean_countries(countries)

    if not rows:
        print("Nothing to export — no records survived cleaning.")
        return None, 0, dropped

    path = build_filename(directory)
    written = write_csv(rows, path)

    return path, written, dropped
