from flask import Flask, render_template, request
import re

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

SPOTIPY_CLIENT_ID = ''
SPOTIPY_CLIENT_SECRET = ''
SPOTIPY_REDIRECT = 'http://127.0.0.1:9090/callback'

app = Flask(__name__)
scope = 'user-top-read,user-library-read,user-read-recently-played'
oauth = SpotifyOAuth(scope=scope, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT)
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET), auth_manager=oauth)

link_pattern = r"https:\/\/open.spotify.com\/([^\/]*)\/([^\?]*)"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submission', methods=['POST'])
def index_post():
    url = request.form['text']
    m = re.match(link_pattern, url)
    if not m:
        return "Expected track, album, playlist, or artist link"
    attributes = collect_attributes(m.group(1), m.group(2))
    return attributes

def collect_attributes(query_type, input_id):
    attributes = []
    match query_type: # python 3.10 feature
        case "track":
            track_att = track_attributes(input_id)
            track_att["name"] = sp.track(input_id)["name"]
            attributes.append(track_att)
        case "album": # annoying that albums, playlists, and artists arrange track info differently
            track_dict = sp.album_tracks(input_id)
            for track in track_dict["items"]:
                track_att = track_attributes(track["id"])
                track_att["name"] = track["name"]
                attributes.append(track_att)
        case "playlist":
            track_dict = sp.playlist_tracks(input_id)
            for track in track_dict["items"]:
                track_att = track_attributes(track["track"]["id"])
                track_att["name"] = track["track"]["name"]
                attributes.append(track_att)
        case "artist":
            track_dict = sp.artist_top_tracks(input_id)
            for track in track_dict["tracks"]:
                track_att = track_attributes(track["id"])
                track_att["name"] = track["name"]
                attributes.append(track_att)
        case _:
            return f"Expected track, album, playlist, or artist; got {query_type}"
    return attributes

def track_attributes(trid):
    attribute_keys = ["danceability","energy","loudness","speechiness","acousticness","liveness","valence"]
    features = sp.audio_features(trid)[0]
    track_att = {key:features[key] for key in attribute_keys}
    track_att["id"] = trid
    return track_att

if __name__ == "__main__":
    app.run(debug=True)
