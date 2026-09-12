"""
Geocoding + routing using free, key-less APIs:
  * Nominatim (OpenStreetMap)  -> address -> lat/lon
  * OSRM public server         -> driving route geometry, distance, duration

Both are free for light use. A short in-process cache and a descriptive
User-Agent keep us within Nominatim's usage policy.
"""

import math
import time
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
PHOTON_URL = "https://photon.komoot.io/api/"
PHOTON_REVERSE_URL = "https://photon.komoot.io/reverse"
HEADERS = {"User-Agent": "TripPilot-AI/1.0 (assessment project)"}

# US place types we treat as "cities" for autocomplete.
US_PLACE_TYPES = {"city", "town", "village", "hamlet", "municipality"}
# Full state name -> USPS abbreviation, for compact suggestion labels.
US_STATES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN",
    "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI",
    "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}

_geocode_cache = {}
_suggest_cache = {}
_reverse_cache = {}


class GeoError(Exception):
    pass


def _short(place, state):
    """("Amarillo", "Texas") -> "Amarillo, TX"; None when there's no place."""
    if not place:
        return None
    state_abbr = US_STATES.get(state, state)
    return f"{place}, {state_abbr}" if state_abbr else place


def geocode(query):
    """Return {'lat', 'lon', 'name', 'short'} for a free-text location."""
    key = query.strip().lower()
    if key in _geocode_cache:
        return _geocode_cache[key]
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1,
                    "addressdetails": 1},
            headers=HEADERS, timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        raise GeoError(f"Geocoding failed for '{query}': {exc}")
    if not data:
        raise GeoError(f"Could not find location: '{query}'")
    hit = data[0]
    addr = hit.get("address", {})
    place = (addr.get("city") or addr.get("town") or addr.get("village")
             or addr.get("hamlet") or addr.get("municipality")
             or addr.get("county"))
    name = hit.get("display_name", query)
    result = {
        "lat": float(hit["lat"]),
        "lon": float(hit["lon"]),
        "name": name,
        "short": _short(place, addr.get("state")) or name.split(",")[0],
    }
    _geocode_cache[key] = result
    time.sleep(1)  # be polite to Nominatim (max 1 req/sec)
    return result


def _photon_reverse(lat, lon, **extra):
    """Properties of Photon's nearest feature to a point ({} on failure).

    The public server answers 503/429 when it's busy, so retry those briefly.
    """
    for attempt in range(3):
        try:
            resp = requests.get(
                PHOTON_REVERSE_URL,
                params={"lat": lat, "lon": lon, "limit": 1, "lang": "en",
                        **extra},
                headers=HEADERS, timeout=6,
            )
            if resp.status_code in (429, 503) and attempt < 2:
                time.sleep(0.6 * (attempt + 1))
                continue
            resp.raise_for_status()
            features = resp.json().get("features", [])
        except (requests.RequestException, ValueError):
            return {}
        return features[0].get("properties", {}) if features else {}
    return {}


def reverse_geocode(lat, lon):
    """Return the nearest town as "City, ST" for a point on the route, or None.

    Uses Photon (no key, no 1 req/sec limit) so the planner can name every
    duty-status change in parallel: the nearest city/town/village within
    30 km, else the county. Results are cached to ~1 km.
    """
    key = (round(lat, 2), round(lon, 2))
    if key in _reverse_cache:
        return _reverse_cache[key]
    props = _photon_reverse(lat, lon, layer="city", radius=30)
    place = props.get("name")
    if not place:
        props = _photon_reverse(lat, lon)
        place = props.get("city") or props.get("town") or props.get("village")
        county = props.get("county")
        if not place and county:
            place = county if "County" in county else f"{county} County"
    name = _short(place, props.get("state"))
    if name:
        _reverse_cache[key] = name
    return name


def suggest_cities(query, limit=7):
    """
    Return up to `limit` US city suggestions for an autocomplete box.
    Each item: {"label": "Dallas, TX", "lat": .., "lon": ..}.
    Uses Photon (a fast OSM type-ahead geocoder) and falls back to Nominatim.
    """
    query = (query or "").strip()
    if len(query) < 2:
        return []
    key = query.lower()
    if key in _suggest_cache:
        return _suggest_cache[key]

    results = _suggest_photon(query, limit) or _suggest_nominatim(query, limit)
    _suggest_cache[key] = results
    return results


def _suggest_photon(query, limit):
    try:
        resp = requests.get(
            PHOTON_URL,
            params={"q": query, "limit": limit * 3, "lang": "en"},
            headers=HEADERS, timeout=8,
        )
        resp.raise_for_status()
        features = resp.json().get("features", [])
    except (requests.RequestException, ValueError):
        return []

    suggestions, seen = [], set()
    for feature in features:
        props = feature.get("properties", {})
        if props.get("countrycode") != "US":
            continue
        if props.get("osm_value") not in US_PLACE_TYPES:
            continue
        name = props.get("name")
        state = props.get("state")
        if not name or not state:
            continue
        label = f"{name}, {US_STATES.get(state, state)}"
        if label in seen:
            continue
        seen.add(label)
        lon, lat = feature.get("geometry", {}).get("coordinates", [None, None])
        suggestions.append({"label": label, "lat": lat, "lon": lon})
        if len(suggestions) >= limit:
            break
    return suggestions


def _suggest_nominatim(query, limit):
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "addressdetails": 1,
                    "countrycodes": "us", "limit": limit,
                    "featuretype": "city"},
            headers=HEADERS, timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return []

    suggestions, seen = [], set()
    for hit in data:
        addr = hit.get("address", {})
        name = (addr.get("city") or addr.get("town") or addr.get("village")
                or addr.get("hamlet") or addr.get("municipality"))
        state = addr.get("state")
        if not name or not state:
            continue
        label = f"{name}, {US_STATES.get(state, state)}"
        if label in seen:
            continue
        seen.add(label)
        suggestions.append({"label": label, "lat": float(hit["lat"]),
                            "lon": float(hit["lon"])})
    return suggestions


def route(points):
    """
    points: list of {'lat','lon'} in order.
    Returns {'geometry': [[lat,lon],...], 'distance_miles', 'duration_hours',
             'legs': [{'distance_miles','duration_hours'}, ...]}.
    """
    coords = ";".join(f"{point['lon']},{point['lat']}" for point in points)
    url = f"{OSRM_URL}/{coords}"
    try:
        resp = requests.get(
            url,
            params={"overview": "full", "geometries": "geojson",
                    "steps": "false"},
            headers=HEADERS, timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        raise GeoError(f"Routing failed: {exc}")
    if data.get("code") != "Ok" or not data.get("routes"):
        raise GeoError("No route found between the given locations.")

    best_route = data["routes"][0]
    geometry = [[lat, lon] for lon, lat in best_route["geometry"]["coordinates"]]
    legs = [{
        "distance_miles": leg["distance"] / 1609.34,
        "duration_hours": leg["duration"] / 3600.0,
    } for leg in best_route["legs"]]
    return {
        "geometry": geometry,
        "distance_miles": best_route["distance"] / 1609.34,
        "duration_hours": best_route["duration"] / 3600.0,
        "legs": legs,
    }


def _haversine_miles(point_a, point_b):
    lat1, lon1, lat2, lon2 = map(
        math.radians, [point_a[0], point_a[1], point_b[0], point_b[1]])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    haversine = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * \
        math.sin(dlon / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(haversine))


def cumulative_miles(geometry):
    """Cumulative mileage at each vertex of the route geometry."""
    cum_miles = [0.0]
    for idx in range(1, len(geometry)):
        cum_miles.append(
            cum_miles[-1] + _haversine_miles(geometry[idx - 1], geometry[idx]))
    return cum_miles


def point_at_mile(geometry, cum_miles, target_mile):
    """Interpolate the [lat,lon] point that lies `target_mile` along the route."""
    if not geometry:
        return None
    total = cum_miles[-1]
    if total <= 0:
        return geometry[0]
    target = max(0.0, min(target_mile, total))
    for idx in range(1, len(cum_miles)):
        if cum_miles[idx] >= target:
            span = cum_miles[idx] - cum_miles[idx - 1] or 1e-9
            fraction = (target - cum_miles[idx - 1]) / span
            prev_pt, next_pt = geometry[idx - 1], geometry[idx]
            lat = prev_pt[0] + fraction * (next_pt[0] - prev_pt[0])
            lon = prev_pt[1] + fraction * (next_pt[1] - prev_pt[1])
            return [lat, lon]
    return geometry[-1]
