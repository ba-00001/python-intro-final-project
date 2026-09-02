"""Country Explorer - a CLI over the World Bank country API.

Stage 1: get the API call working and prove data is coming back.
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


def main():
    rows = fetch_data("country")

    if rows is None:
        print("Cannot continue without data. Exiting.")
        return

    print(f"Fetched {len(rows)} rows from the API.")
    print(f"First row name: {rows[0]['name']}")


if __name__ == "__main__":
    main()
