import os
from pathlib import Path
import re
import sys
import genimg
import ollamagen
import json
import random
import util
import imgprocessor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # avoids crashes on fancy chars

with open("config.json", "r") as f:
    config = json.load(f)

theme = random.choice(config["themes"])
genre = random.choice(config["genres"])
imgprompt = config["imgprompt"]
imgnegativeprompt = config["imgnegativeprompt"]
prompt = config["prompt"].format(themes=theme, genres=genre)


print(f"Selected Theme: {theme}")
print(f"Selected Genre: {genre}")

res = ollamagen.ollama_generate(
    model="qwen3:8b",
    prompt=prompt,
    options={
        "temperature": 0.8,
        "num_ctx": 8192,
    },
    think= False,
)


cleaned_text = re.sub(r"<think>.*?</think>", "", res["response"], flags=re.DOTALL)
gameidea = cleaned_text.strip()

print("Game Idea:", gameidea)


jsontemplate = """
{
  "name": "",
  "description": "",
  "images": [
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
    { "file": "", "shortgenerationprompt": "" },
  ]
}
"""

res = ollamagen.ollama_generate(
    model="qwen3:8b",
    prompt="Here is my game idea \n" + gameidea + "\n" + "Fill this json template"  + "\n"+ jsontemplate,
    options={
        "temperature": 0.5,
        "num_ctx": 8192,
    },
    think= False,
)

print("Ollama response:", res)
json_data_raw = res["response"]
print("JSON Data:", json_data_raw)

# Extract JSON data from the response
json_data = util.extract_json_from_llm_answer(json_data_raw)
print("Extracted JSON Data:", json_data)

# create the directory if it doesn't exist
os.makedirs("games", exist_ok=True)
# create the game directory

game_dir = os.path.join("games", json_data["name"])

if not os.path.exists(game_dir):
    game_dir = game_dir.replace(":", "-")  # Replace ':' with '-' to avoid invalid directory name

os.makedirs(game_dir, exist_ok=True)


for i in json_data["images"]:
    promparg = i["shortgenerationprompt"] + ", " + imgprompt
    negparg = imgnegativeprompt

    path = genimg.generate_image(
        outfile="games/"+ json_data["name"].replace(":", "-") + "/images/" + i["file"],
        prompt=promparg,
        negativeprompt=negparg,
        model="OfficialStableDiffusion/dreamshaper_8LCM",
        seed=-1,
        steps=5,
        cfgscale=2.0,
        aspectratio="1:1",
        width=512,
        height=512,
        sampler="lcm",
        automaticvae=True,
        images=1
    )
    print(f"Generated image saved to: {path}")

# Process the images in the game directory
img_dir = os.path.join(game_dir, "images")
imglist = imgprocessor.process_images(Path(img_dir))

imagelistwithdescription = []
for i in range(len(imglist)):
    filename = os.path.basename(imglist[i])
    parent = os.path.basename(os.path.dirname(imglist[i]))
    imagelistwithdescription.append(f"path: {parent}/{filename} description: {json_data['images'][i]['shortgenerationprompt']}")

imgliststr = "\n".join(imagelistwithdescription)

gamegenprompt = f"""
Task

Create an HTML5 canvas game based on the game description provided below.
Constraints

    Single file only: One .html file containing all HTML, CSS, and JavaScript.

    No external libraries or files beyond those listed in the assets section below.

    Max size: ~500 lines of code (including HTML/CSS/JS). Keep comments concise.

    Canvas size: 1024 × 720.

    Images: Image dimensions are indicated in each asset’s name. You may resize images at runtime to fit gameplay.

    Offline-ready: The file must run locally in a browser with no additional setup.

Assets
    List of available images :
    {imgliststr}

Output Requirements

    A complete, runnable single HTML file with embedded <style> and <script>.

    Clear initialization code that sets up the 1024×720 canvas and game loop.

    Basic input handling (keyboard/mouse/touch as appropriate).

    Simple audio is optional; if used, it must be embedded (e.g., base64) and counted within the 500 lines.

    Include minimal UI (start/restart, score/lives, instructions).

Quality Bar

    Stable 60 FPS on a typical desktop.

    Clean structure (modules via IIFEs or simple classes/objects), no frameworks.

Deliverable

Return only the single HTML file content.

Game Description
{gameidea}
"""


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



res = ollamagen.ollama_generate(
    model="qwen3-coder:latest",
    prompt=gamegenprompt,
    options={
        "temperature": 0.6,
        "num_ctx": 8192,
    },
    stream=True,
    on_chunk=on_chunk,
)


try:
    while True:
        next(res)
except StopIteration as fin:
    res = fin.value

print("\n=== FINAL RESULT ===\n")


# save the generated HTML file
html_content = res["response"]
print("Generated HTML content:", html_content)
# get inner html content
html_content = util.extract_html_block(html_content)


html_file_path = os.path.join(game_dir, "game.html")
with open(html_file_path, "w", encoding="utf-8") as f:
    f.write(html_content)
# Save the game idea and JSON data to a text file
game_info_path = os.path.join(game_dir, "game_info.txt")
with open(game_info_path, "w", encoding="utf-8") as f:
    f.write(f"Game Idea:\n{gameidea}\n\n")
    f.write("JSON Data:\n")
    json.dump(json_data, f, indent=2)

prompt_path = os.path.join(game_dir, "prompt.txt")
with open(prompt_path, "w", encoding="utf-8") as f:
    f.write(gamegenprompt)

#generate thumbnail
thumbnail_path = os.path.join(game_dir, "thumbnail.png")
genimg.generate_image(
    outfile=thumbnail_path,
    prompt=f"A thumbnail for the game {json_data["name"]}, {imgprompt}",
    negativeprompt=imgnegativeprompt,
    model="OfficialStableDiffusion/dreamshaper_8LCM",
    seed=-1,
    steps=5,
    cfgscale=2.0,
    aspectratio="1:1",
    width=512,
    height=512,
    sampler="lcm",
    automaticvae=True,
    images=1
)
