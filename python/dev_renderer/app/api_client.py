import requests

def fetch_packing_result(api_url: str, payload: dict) -> dict:
        response = requests.post(api_url, json=payload, timeout=10)
        print(response.text)
        response.raise_for_status()
        return response.json()