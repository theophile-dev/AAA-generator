import requests
import json
import os

BASE_URL = "http://localhost:7801"
OUTPUT_FILE = "t2i_params_ids.json"

def get_session_id(base_url=BASE_URL) -> str:
    """Get a new session ID from the API."""
    url = f"{base_url}/API/GetNewSession"
    resp = requests.post(url, json={}, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    session_id = data.get("session_id")
    if not session_id:
        raise RuntimeError(f"No session_id in response: {data}")
    return session_id

def list_t2i_param_ids(base_url=BASE_URL, output_file=OUTPUT_FILE):
    """Fetch T2I parameters and save only their IDs."""
    session_id = get_session_id(base_url)
    url = f"{base_url}/API/ListT2IParams"
    payload = {"session_id": session_id}

    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()

    data = resp.json()

    # Extract only the "id" values
    ids = []
    if isinstance(data, dict) and "list" in data:
        ids = [item["id"] for item in data["list"] if "id" in item]

    # Save as JSON array
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(ids)} IDs to {os.path.abspath(output_file)}")
    return ids

if __name__ == "__main__":
    ids = list_t2i_param_ids()
    print(json.dumps(ids, indent=2))
