import httpx

METEO_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm + hail", 99: "Heavy thunderstorm + hail",
}


async def _fetch(lat: float, lon: float) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(METEO_URL, params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,wind_speed_10m,weathercode",
                "wind_speed_unit": "kmh",
            })
            resp.raise_for_status()
            current = resp.json().get("current", {})
            code = current.get("weathercode", 0)
            return {
                "condition": WMO_CODES.get(code, "Unknown"),
                "temperature_c": current.get("temperature_2m"),
                "wind_kmh": current.get("wind_speed_10m"),
            }
    except Exception:
        return None


async def get_weather(pickup_lat: float, pickup_lon: float,
                      dest_lat: float, dest_lon: float) -> dict:
    pickup_wx, dest_wx = None, None
    if pickup_lat and pickup_lon:
        pickup_wx = await _fetch(pickup_lat, pickup_lon)
    if dest_lat and dest_lon:
        dest_wx = await _fetch(dest_lat, dest_lon)
    return {"pickup": pickup_wx, "destination": dest_wx}
