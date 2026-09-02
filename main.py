"""Country Explorer - a CLI over the World Bank country API.

Stage 2: parse the two endpoints into one clean list of dictionaries.
"""

import requests

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


def main():
    print("Fetching country data from the World Bank API...")

    countries = load_countries()

    if countries is None:
        print("Cannot continue without data. Exiting.")
        return

    print(f"Loaded {len(countries)} countries.")

    with_population = 0

    for country in countries:
        if country["population"] > 0:
            with_population += 1

    print(f"{with_population} have a population figure.")
    print(f"Example: {countries[0]}")


if __name__ == "__main__":
    main()
