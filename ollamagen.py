import requests
import json
from typing import Dict, Generator, Iterable, Optional, Union

class OllamaStreamError(RuntimeError):
    pass

def _iter_ollama_lines(resp: requests.Response):
    # Option A: let requests use its default newline delimiter
    for raw in resp.iter_lines(decode_unicode=True):  # <-- removed delimiter="\n"
        if not raw:
            continue
        try:
            yield json.loads(raw)
        except json.JSONDecodeError as e:
            raise OllamaStreamError(f"Invalid JSON line from stream: {raw}") from e


def ollama_generate(
    model: str,
    prompt: str,
    base_url: str = "http://localhost:11434/api/generate",
    stream: bool = False,
    timeout: int = 300,
    session: Optional[requests.Session] = None,
    on_chunk: Optional[callable] = None,
    **extra_params
) -> Union[Dict, Generator[str, None, Dict]]:
    """
    Call Ollama's /api/generate endpoint.

    Modes:
      - stream=False (default): returns a single parsed JSON dict.
      - stream=True: returns a generator that yields incremental text chunks.
                     When the stream finishes, the generator's StopIteration
                     'value' is the final JSON dict (including timings/metadata).

    Args:
        model: e.g. "llama3.2".
        prompt: The text prompt for generation.
        base_url: Ollama API generate endpoint (default localhost).
        stream: Whether to stream partial outputs.
        timeout: Requests timeout (seconds).
        session: Optional requests.Session for connection reuse.
        on_chunk: Optional callback called with each text chunk (string).
        **extra_params: Any extra parameters Ollama accepts (e.g., 'options').

    Returns:
        - Non-streaming: Dict with full response.
        - Streaming: Generator[str] yielding text chunks; StopIteration.value is final Dict.

    Raises:
        requests.HTTPError for non-2xx responses.
        RuntimeError / OllamaStreamError for parsing issues.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream
    }
    payload.update(extra_params)

    sess = session or requests.Session()
    resp = sess.post(base_url, json=payload, timeout=timeout, stream=stream)
    resp.raise_for_status()

    if not stream:
        # Non-streaming mode: server returns a single JSON object.
        try:
            return resp.json()
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON response: {resp.text}")

    # Streaming mode: newline-delimited JSON objects.
    def gen() -> Generator[str, None, Dict]:
        final_payload: Dict = {}
        accumulated_text_parts = []

        try:
            for obj in _iter_ollama_lines(resp):
                # Typical fields per chunk: {"model": "...", "created_at": "...",
                #   "response": "partial text", "done": false, ...}
                if "response" in obj:
                    chunk = obj["response"]
                    accumulated_text_parts.append(chunk)
                    if on_chunk:
                        try:
                            on_chunk(chunk)
                        except Exception:
                            # Swallow user callback errors to avoid breaking the stream
                            pass
                    yield chunk

                # The last object has "done": true and timing/usage metadata.
                if obj.get("done"):
                    # Build a final combined payload similar to non-streaming shape.
                    final_payload = obj.copy()
                    final_payload["response"] = "".join(accumulated_text_parts)
                    # Some clients prefer top-level model/prompt back for convenience:
                    final_payload.setdefault("model", payload.get("model"))
                    break
        finally:
            # Ensure the connection is closed even if the consumer stops early.
            resp.close()

        return final_payload  # becomes StopIteration.value

    return gen()
