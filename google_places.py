
import requests
import pandas as pd
import requests
import pandas as pd
import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def get_place_details(place_id):

    url = (
        "https://maps.googleapis.com/maps/api/place/details/json"
    )

    params = {
        "place_id": place_id,
        "fields": (
            "name,rating,reviews,"
            "user_ratings_total"
        ),
        "key": GOOGLE_API_KEY
    }

    response = requests.get(
        url,
        params=params
    )

    result = response.json()

    return result.get("result", {})
API_KEY = "AIzaSyCtRb4T5P0jjzUsscW1EJOJfX3n8Uae7E8"


def search_places(keyword, lat, lon, radius=5000):

    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": (
            "places.displayName,"
            "places.location,"
            "places.rating,"
            "places.userRatingCount,"
            "places.formattedAddress"
        )
    }

    body = {
        "textQuery": keyword,
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lon
                },
                "radius": radius
            }
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=body
    )

    data = response.json()

    results = []

    for place in data.get("places", []):

        results.append({
            "name": place.get("displayName", {}).get("text"),
            "lat": place["location"]["latitude"],
            "lon": place["location"]["longitude"],
            "rating": place.get("rating", 0),
            "reviews": place.get("userRatingCount", 0),
            "address": place.get("formattedAddress"),
            "place_id": place.get("place_id"),
        })

    return pd.DataFrame(results)


# ==================================================
# CONTAR LUGARES CERCANOS
# ==================================================

def count_nearby_places(keyword, lat, lon, radius=3000):

    df = search_places(
        keyword=keyword,
        lat=lat,
        lon=lon,
        radius=radius
    )

    return len(df)