import httpx

from nascopilot.config import settings

ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"


async def get_route_eta(
    start_lat: float, start_lon: float, end_lat: float, end_lon: float
) -> dict | None:
    if not settings.ors_api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                ORS_URL,
                headers={
                    "Authorization": settings.ors_api_key,
                    "Content-Type": "application/json",
                },
                json={"coordinates": [[start_lon, start_lat], [end_lon, end_lat]]},
            )
            resp.raise_for_status()
            data = resp.json()
            summary = data["routes"][0]["summary"]
            return {
                "distance_km": round(summary["distance"] / 1000, 1),
                "duration_min": round(summary["duration"] / 60),
            }
    except Exception:
        return None
