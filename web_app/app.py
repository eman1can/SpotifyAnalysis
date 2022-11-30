import json

import pandas as pd
from flask import Flask, render_template, request
import re

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from spotipy_client import SpotipyClient
from util import load_json
from pickle import load as pk_load

LIVE_QUERY = False
SPOTIPY_REDIRECT = 'http://127.0.0.1:9090/callback'

app = Flask(__name__)
scope = 'user-top-read,user-library-read,user-read-recently-played'

link_pattern = r"https:\/\/open.spotify.com\/([^\/]*)\/([^\?]*)"

import numpy as np

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submission', methods=['POST'])
def index_post():
    url = ''
    client_id = ''
    client_secret = ''
    attributes = None
    if request.form['submit'] == "Live":
        url = request.form['link']
        client_id = request.form['client_id']
        client_secret = request.form['client_secret']

        oauth = SpotifyOAuth(scope=scope, client_id=client_id, client_secret=client_secret, redirect_uri=SPOTIPY_REDIRECT)
        sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret), auth_manager=oauth)

        m = re.match(link_pattern, url)
        if not m:
            return "Expected track, album, playlist, or artist link"
        attributes = collect_attributes(sp, m.group(1), m.group(2))
        if isinstance(attributes, str):
            with open('web_app/templates/results.html', 'r') as file:
                parts = file.read().split('|')

            output = parts[0]
            output += client_id
            output += parts[1]
            output += client_secret
            output += parts[2]
            output += url
            output += parts[3]
            output += f'<h3>Error: {attributes}</h3>' + parts[4]
            return output
        # f1 = open("./demo.json", "w")
        # json.dump(attributes, f1, indent=4)
        # f1.close()
    elif request.form['submit'] == "Demo":
        with open("web_app/demo.json") as f:
            attributes = json.load(f)
    print(attributes)
    dataset = []
    tinfo = []
    for ix, track in enumerate(attributes):
        tinfo.append((
            track['id'],
            track['name'],
            f"{int(track['duration_ms'] / 60000)}:" + str(int((track['duration_ms'] % 60000) / 1000)).zfill(2)
        ))
        dataset.append([
            track['listenCount'],
            track['tempo'],
            track['danceability'],
            track['energy'],
            track['loudness'],
            track['speechiness'],
            track['acousticness'],
            track['liveness'],
            track['valence']
        ])
    df = pd.DataFrame(dataset)
    # TODO: Apply Normalization

    with open('model.pickle', 'rb') as file:
        model = pk_load(file)

    def minmax_scale(A):
        min = np.amin(A)
        max = np.amax(A)
        return (A - min) / (max - min)

    def regularize(A):
        if np.sum(A) == 0:
            return A
        return minmax_scale(A)

    # Regularize columns
    print(df)
    df.to_csv('test.csv')
    df[4] = 10 ** (df[4] / 20)
    df[0] = regularize(df[0])
    df[1] = regularize(df[1])
    print(df)
    yh = model.predict(df)
    print(yh)
    # yh = [1 for _ in range(len(attributes))]

    with open('web_app/templates/results.html', 'r') as file:
        parts = file.read().split('|')

    output = parts[0]
    output += client_id
    output += parts[1]
    output += client_secret
    output += parts[2]
    output += url
    output += parts[3]

    output += """<table><tr style="width: 15%"><th>Index</th><th>Song Name</th><th>Duration</th><th>Will Like?</th></tr>"""
    for ix, (track_id, track_name, duration) in enumerate(tinfo):
        liked = 'Yes' if yh[ix] == 1 else 'No'
        output += f'<tr style="width: 15%"><td>{ix}</td><td>{track_name}</td><td>{duration}</td><td>{liked}</td></tr>'

    return output + '</table>' + parts[4]

def collect_attributes(sp, query_type, input_id):
    if query_type == "track":
        tr_ids = [input_id]
        names = [sp.track(input_id)["name"]]
    elif query_type == "album":  # annoying that albums, playlists, and artists arrange track info differently
        track_dict = sp.album_tracks(input_id)
        tr_ids = [track["id"] for track in track_dict["items"]]
        names = [track["name"] for track in track_dict["items"]]
    elif query_type == "playlist":
        track_dict = sp.playlist_tracks(input_id)
        tr_ids = [track["track"]["id"] for track in track_dict["items"]]
        names = [track["track"]["name"] for track in track_dict["items"]]
    elif query_type == "artist":
        track_dict = sp.artist_top_tracks(input_id)
        tr_ids = [track["id"] for track in track_dict["tracks"]]
        names = [track["name"] for track in track_dict["tracks"]]
    else:
        return f"Expected track, album, playlist, or artist; got {query_type}"
    return track_attributes(sp, tr_ids, names)


def track_attributes(sp, tr_ids, names):
    attribute_keys = ["key", "tempo", "danceability", "energy", "loudness", "speechiness", "acousticness", "liveness", "valence"]
    client = SpotipyClient()
    track_info = list(client.get_track_information(tr_ids).values())
    features = list(client.get_audio_features(tr_ids).values())
    listened_songs = [x['trackId'] for x in load_json('listened_songs.json')]
    track_atts = [{key: f_ls[key] for key in attribute_keys} for f_ls in features]
    for i_tr in range(len(tr_ids)):
        track_atts[i_tr]["id"] = tr_ids[i_tr]
        track_atts[i_tr]["name"] = names[i_tr]
        track_atts[i_tr]["duration_ms"] = track_info[i_tr]['duration_ms']
        track_atts[i_tr]["listenCount"] = listened_songs.count(tr_ids[i_tr])
    return track_atts


if __name__ == "__main__":
    app.run(debug=True)
