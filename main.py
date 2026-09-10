"""Country Explorer - a CLI over the World Bank country API.

Search by name, filter a region by population, compare two countries, or
export the cleaned data to CSV.
"""

import requests

# The Week 11 extension lives in its own module - cleaning and exporting is a
# different job from fetching and browsing.
from export import export_countries

# Base URL kept separate from the paths so the two endpoints below don't repeat
# it, and there's one place to change if the API moves.
BASE_URL = "https://api.worldbank.org/v2"

# Every World Bank response needs format=json or it answers with XML.
DEFAULT_PARAMS = {"format": "json", "per_page": 400}


def fetch_data(path, params=None):
    """GET one endpoint and return its list of rows, or None on failure.

    path is appended to BASE_URL. params are merged over DEFAULT_PARAMS, so
    callers only pass what differs.
    """
    # Merging rather than replacing means format=json can't be forgotten by a
    # caller. Passing query parameters as an argument - instead of baking them
    # into the URL string - is what lets one function serve both endpoints.
    query = dict(DEFAULT_PARAMS)

    if params:
        query.update(params)

    url = f"{BASE_URL}/{path}"

    try:
        # timeout matters: without it a server that accepts the connection and
        # then never replies hangs the program with nothing to catch.
        response = requests.get(url, params=query, timeout=30)
    except requests.exceptions.RequestException as e:
        # Base class of requests' own errors, so this covers connection
        # failures, DNS problems and timeouts alike. The user's next step is
        # the same for all of them.
        print(f"Error: could not reach the API ({type(e).__name__}).")
        return None

    if response.status_code != 200:
        print(f"Error: API returned status {response.status_code}, expected 200.")
        return None

    payload = response.json()

    # A 200 does not guarantee usable data. The API this project originally
    # targeted (restcountries.com) returned 200 with a deprecation notice in
    # place of results, which is exactly how I learned to check the shape and
    # not just the status.
    #
    # The World Bank wraps everything as [metadata, [rows]], so anything that
    # isn't a two-item list is not a response I can read.
    if not isinstance(payload, list) or len(payload) < 2:
        print("Error: unexpected response shape from the API.")
        return None

    return payload[1]


def fetch_populations():
    """Return {ISO3 code: latest population} for every country with a figure."""
    # mrnev=1 means "most recent non-empty value", so the API picks the latest
    # year that actually has data instead of me requesting a year and hoping.
    rows = fetch_data(
        "country/all/indicator/SP.POP.TOTL",
        {"mrnev": 1},
    )

    if rows is None:
        return None

    populations = {}

    for row in rows:
        # Even with mrnev=1, a country with no data at all comes back with
        # value None. .get() plus this check means one gap doesn't take out
        # the whole dictionary.
        value = row.get("value")

        # Keyed by ISO3, because that is what the country endpoint calls "id".
        # Both endpoints have a field named id, but they hold DIFFERENT
        # identifiers - the population rows put a World Bank code ("ZH", "1A")
        # in country.id and keep ISO3 in countryiso3code. Joining on the wrong
        # one matches nothing and fails silently, leaving every population at
        # the default. That cost me a while to spot.
        iso3 = row.get("countryiso3code")

        if value is None or not iso3:
            continue

        populations[iso3] = int(value)

    return populations


def process_data(rows, populations):
    """Turn raw API rows into a list of dicts with just the fields I need."""
    countries = []

    for row in rows:
        # The country list includes aggregates like "Arab World" and "Euro
        # area", which are not countries. They are all labelled with the region
        # "Aggregates", so this leaves only real ones.
        region = row["region"]["value"].strip()

        if region == "Aggregates":
            continue

        # capitalCity exists but is an empty string for some territories.
        # Empty is falsy, so `or` covers both that and a missing key, and the
        # display shows N/A rather than a blank column.
        capital = row.get("capitalCity") or "N/A"

        countries.append(
            {
                "name": row["name"],
                "capital": capital,
                "region": region,
                "income_level": row["incomeLevel"]["value"].strip(),
                # 0 rather than None so sorting and formatting never have to
                # special-case it. The export step treats 0 as missing.
                "population": populations.get(row["id"], 0),
            }
        )

    return countries


def load_countries():
    """Fetch both endpoints and combine them. Returns None on failure."""
    rows = fetch_data("country")

    if rows is None:
        return None

    populations = fetch_populations()

    if populations is None:
        return None

    return process_data(rows, populations)


def format_country(country):
    """Return one country as a single readable line."""
    # :, adds thousands separators so 9092436 reads as 9,092,436.
    population = f"{country['population']:,}" if country["population"] else "unknown"

    return (
        f"{country['name']} — Capital: {country['capital']} "
        f"| Region: {country['region']} "
        f"| Population: {population}"
    )


def display_results(results):
    """Print a list of countries, or say there were none."""
    if not results:
        print("No matches found.")
        return

    for country in results:
        print(f"  {format_country(country)}")

    # Singular/plural so the count doesn't read "1 results".
    print(f"  ({len(results)} result{'s' if len(results) != 1 else ''})")


def search_by_name(countries, term):
    """Return countries whose name contains term, ignoring case."""
    term = term.lower()

    # `in` on strings is a substring test, so this is a partial match:
    # "land" finds Finland, Iceland, Ireland, Poland.
    return [c for c in countries if term in c["name"].lower()]


def filter_by_region(countries, region_term):
    """Return countries in a region, largest population first."""
    region_term = region_term.lower()

    # Partial match so "europe" finds "Europe & Central Asia" without the user
    # having to type the World Bank's full region name.
    matches = [c for c in countries if region_term in c["region"].lower()]

    # sorted() returns a new list rather than reordering the caller's.
    return sorted(matches, key=lambda c: c["population"], reverse=True)


def find_one(countries, term):
    """Return the single best name match, or None if it's absent or ambiguous."""
    matches = search_by_name(countries, term)

    if not matches:
        print(f"No country matching '{term}'.")
        return None

    # An exact name match wins over a partial one, so "Chad" doesn't get
    # confused by a longer name that contains it.
    for country in matches:
        if country["name"].lower() == term.lower():
            return country

    if len(matches) > 1:
        names = ", ".join(c["name"] for c in matches[:5])
        print(f"'{term}' is ambiguous — did you mean: {names}?")
        return None

    return matches[0]


def compare_countries(countries, first_term, second_term):
    """Print a side-by-side comparison of two countries."""
    first = find_one(countries, first_term)
    second = find_one(countries, second_term)

    # find_one already explained what went wrong, so just stop.
    if first is None or second is None:
        return

    print()
    for country in (first, second):
        print(f"  {format_country(country)}")

    # abs() so the difference reads the same regardless of which was named
    # first, with the larger one stated explicitly instead of implied by sign.
    difference = abs(first["population"] - second["population"])
    larger = first if first["population"] > second["population"] else second

    print()
    print(f"  {larger['name']} is larger by {difference:,} people.")


def show_menu():
    """Print the menu and return the user's choice as a string."""
    print()
    print("=== Country Explorer ===")
    print("1. Search by name")
    print("2. Filter by region (sorted by population)")
    print("3. Compare two countries")
    print("4. Export cleaned data to CSV")
    print("5. Quit")
    # Returns text, not an int, so typing "abc" falls through to the else
    # instead of crashing on int().
    return input("Choose an option (1-5): ").strip()


def main():
    print("Fetching country data from the World Bank API...")

    countries = load_countries()

    # load_countries already printed the reason, so exit rather than carry on
    # with nothing to search.
    if countries is None:
        print("Cannot continue without data. Exiting.")
        return

    print(f"Loaded {len(countries)} countries.")

    running = True

    while running:
        choice = show_menu()

        if choice == "1":
            term = input("Search: ").strip()

            if not term:
                print("Please enter something to search for.")
            else:
                display_results(search_by_name(countries, term))

        elif choice == "2":
            region = input("Region: ").strip()

            if not region:
                print("Please enter a region name.")
            else:
                display_results(filter_by_region(countries, region))

        elif choice == "3":
            first = input("First country: ").strip()
            second = input("Second country: ").strip()

            if not first or not second:
                print("Please name two countries.")
            else:
                compare_countries(countries, first, second)

        elif choice == "4":
            path, written, dropped = export_countries(countries)

            if path:
                print(f"Wrote {written} rows to {path}")
                # Reporting what was discarded matters as much as what was
                # kept. A silent export looks identical whether it dropped
                # nothing or half the dataset.
                print(f"Dropped {dropped} records that failed cleaning.")

        elif choice == "5":
            print("Goodbye!")
            running = False

        else:
            # Covers empty input and anything that isn't 1-5, so a stray
            # keystroke re-shows the menu instead of crashing.
            print("Please choose a number from 1 to 5.")


if __name__ == "__main__":
    main()
