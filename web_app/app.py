from flask import Flask, render_template, request
from spotipy_client import SpotipyClient
import re

import spotipy
import spotipy.util as util
from spotipy import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

SPOTIPY_CLIENT_ID = ''
SPOTIPY_CLIENT_SECRET = ''

app = Flask(__name__)
scope = 'user-top-read,user-library-read,user-read-recently-played'
oauth = SpotifyOAuth(scope=scope, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri='http://127.0.0.1:9090')
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET), auth_manager=oauth)

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
    attributes = None
    input_id = m.group(2)

    match m.group(1): # python 3.10 feature
        case "track":
            attributes = sp.track(input_id)
        case "album":
            attributes = sp.album(input_id)
        case "playlist":
            attributes = sp.playlist(input_id)
        case "artist":
            attributes = sp.artist(input_id)
        case _:
            return "Expected track, album, playlist, or artist link"
        
    print(attributes)
    return processed_text

if __name__ == "__main__":
    app.run(debug=True)
