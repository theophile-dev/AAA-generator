import sys
import ollamagen  # assumes your upgraded ollamagen.ollama_generate is available

accumulated = []
chunk_count = 0  # keep track of how many chunks we've seen

def on_chunk(piece: str) -> None:
    """Append each chunk and print only every 150th chunk received."""
    global chunk_count
    chunk_count += 1
    accumulated.append(piece)

    if chunk_count % 150 == 0:
        full_so_far = "".join(accumulated)
        print(f"\n--- streaming update after {chunk_count} chunks ---\n")
        print(full_so_far, flush=True)

# Start the streaming request
gen = ollamagen.ollama_generate(
    model="qwen3-coder:latest",
    prompt=(
        "write a small html game with a simple mechanic. "
        "The game should be fun and engaging, suitable for a wide audience. "
        "Respond only with the code, no dependy required the game should be runnable."
    ),
    options={
        "temperature": 0.6,
        "num_ctx": 8192,
    },
    stream=True,
    on_chunk=on_chunk,
)

# Exhaust the generator to completion
try:
    while True:
        next(gen)
except StopIteration as fin:
    res = fin.value

print("\n=== FINAL RESULT ===\n")
print(res["response"])
print("\nOllama response object (metadata):")
print(res)
