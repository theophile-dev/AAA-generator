import os
from pathlib import Path
import json

def inject_gamelist_into_html(json_data, html_path, output_path=None):

    # Read the HTML file
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Convert the JSON data to a JSON string for embedding in JavaScript
    json_str = json.dumps(json_data, ensure_ascii=False)

    # Replace {gamelist} placeholder with actual JSON string
    updated_html = html_content.replace('{gamelist}', json_str)

    # Save to output file or overwrite the original
    if not output_path:
        output_path = html_path
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(updated_html)

    return output_path


BASE_DIR = "games"  # folder containing all game subfolders
games_data = []

for game_name in os.listdir(BASE_DIR):
    game_dir = os.path.join(BASE_DIR, game_name)

    if os.path.isdir(game_dir):
        game_html_path = os.path.join(game_dir, "game.html")
        thumbnail_path = os.path.join(game_dir, "thumbnail.png")

        if os.path.exists(game_html_path):
            game_html_url = BASE_DIR+'/'+game_name+'/'+"game.html"


            thumbnail_url = None
            if os.path.exists(thumbnail_path):
                thumbnail_url = BASE_DIR+'/'+game_name+'/'+"thumbnail.png"
               

            games_data.append({
                "name": game_name,
                "game_html": game_html_url,
                "thumbnail": thumbnail_url
            })




template_file = Path("index.template.html")
index_file = Path("index.html")

# Read the template HTML
html_template_content = template_file.read_text(encoding="utf-8")

# Replace placeholder with JSON data
json_str = json.dumps(games_data, ensure_ascii=False)
updated_html = html_template_content.replace("{gamelist}", json_str)

# Write back the updated HTML
index_file.write_text(updated_html, encoding="utf-8")

