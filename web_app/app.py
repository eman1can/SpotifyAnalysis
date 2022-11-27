from flask import Flask, render_template, request
import re

app = Flask(__name__)

link_pattern = r"https:\/\/open.spotify.com\/([^\/]*)\/([^\?]*)"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submission', methods=['POST'])
def index_post():
    text = request.form['text']
    m = re.match(link_pattern, text)
    if not m:
        return "Invalid submission"

    processed_text = ""
    input_id = m.group(2)
    
    match m.group(1): # python 3.10 feature
        case "track":
            processed_text = "track: " + input_id
        case "album":
            processed_text = "album: " + input_id
        case "playlist":
            processed_text = "playlist: " + input_id
        case "artist":
            processed_text = "artist: " + input_id
        case _:
            return "Expected track, album, playlist, or artist link"
    
    return processed_text

if __name__ == "__main__":
    app.run(debug=True)
