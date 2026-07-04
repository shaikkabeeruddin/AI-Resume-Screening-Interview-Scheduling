import requests
from app.config import settings


def create_candidate_record(payload: dict) -> dict:
    url = f"{settings.NOCODB_BASE_URL}{settings.NOCODB_TABLE_PATH}"

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "xc-token": settings.NOCODB_TOKEN
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)

    if response.status_code >= 400:
        raise Exception(
            f"NocoDB error {response.status_code}: {response.text} | payload={payload}"
        )

    return response.json()