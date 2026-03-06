import httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
RADIUS_M = 20_000  # 20 km


async def get_nearby_facilities(lat: float, lon: float) -> list[dict]:
    query = f"""
    [out:json][timeout:15];
    (
      node["amenity"="hospital"](around:{RADIUS_M},{lat},{lon});
      node["amenity"="clinic"](around:{RADIUS_M},{lat},{lon});
      way["amenity"="hospital"](around:{RADIUS_M},{lat},{lon});
      way["amenity"="clinic"](around:{RADIUS_M},{lat},{lon});
    );
    out center 10;
    """
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            resp.raise_for_status()
            elements = resp.json().get("elements", [])
    except Exception:
        return []

    facilities = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("amenity", "Unknown facility")
        if el["type"] == "node":
            f_lat, f_lon = el.get("lat"), el.get("lon")
        else:
            center = el.get("center", {})
            f_lat, f_lon = center.get("lat"), center.get("lon")
        facilities.append({
            "name": name,
            "type": tags.get("amenity", "hospital"),
            "lat": f_lat,
            "lon": f_lon,
        })

    return facilities[:5]
