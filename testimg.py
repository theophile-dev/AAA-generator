from pathlib import Path

from imgprocessor import process_images

# Process the "Jungle Puzzle Expedition" images
outputs = process_images(
    Path("games\Jungle Puzzle Expedition"),
    rgb_min=240, v_min=0.95, s_max=0.20,
    feather=1, pad=1
)

print("Processed files:")
for p in outputs:
    print(p)