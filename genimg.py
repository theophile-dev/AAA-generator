import os
import requests
from urllib.parse import urljoin

def generate_image(
    outfile: str,
    base_url: str = "http://localhost:7801",
    **params
) -> str:
    """
    Generate an image from a local text-to-image server and save it.

    Args:
        outfile: Path to save the image.
        base_url: Base URL of the API server.
        **params: Any parameters supported by the API.
                  Example:
                  prompt="a cool cat",
                  model="OfficialStableDiffusion/dreamshaper_8LCM",
                  seed=1884268507,
                  steps=5,
                  cfgscale=2.0,
                  aspectratio="1:1",
                  width=512,
                  height=512,
                  sampler="lcm",
                  automaticvae=True,
                  negativeprompt=""

    Returns:
        The absolute path to the saved image file.
    """

    # Step 1: Get a new session ID
    session_url = urljoin(base_url, "/API/GetNewSession")
    sid_resp = requests.post(session_url, json={}, timeout=60)
    sid_resp.raise_for_status()
    session_id = sid_resp.json().get("session_id")
    if not session_id:
        raise RuntimeError(f"No session_id in response: {sid_resp.text}")

    # Step 2: Generate the image
    payload = {"session_id": session_id}
    payload.update(params)  # add all user-specified API params

    gen_url = urljoin(base_url, "/API/GenerateText2Image")
    gen_resp = requests.post(gen_url, json=payload, timeout=300)
    gen_resp.raise_for_status()
    data = gen_resp.json()

    image_paths = data.get("images")
    if not image_paths:
        raise RuntimeError(f"No images returned: {data}")

    first_image_path = image_paths[0]
    if not first_image_path.startswith("http"):
        first_image_path = urljoin(base_url + "/", first_image_path.lstrip("/"))

    # Step 3: Download the image
    img_resp = requests.get(first_image_path, timeout=300)
    img_resp.raise_for_status()

    os.makedirs(os.path.dirname(os.path.abspath(outfile)) or ".", exist_ok=True)
    with open(outfile, "wb") as f:
        f.write(img_resp.content)

    return os.path.abspath(outfile)
