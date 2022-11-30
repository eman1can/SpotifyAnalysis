import pprint

from spotipy_client import SpotipyClient
from util import load_json, save_json, json_exists

pp = pprint.PrettyPrinter()
datapath = '../Data/'

client = SpotipyClient()

# This data is *slightly* wrong. First, recently listened songs won't have correct msPlayed for songs that were skipped
# Second, the artistName is only the *first* artist on the label, not all.
liked_song_records = client.get_liked_songs()
listened_song_records = client.get_listened_songs()

print('Getting Track Information')
track_information = {}
if json_exists('track_information.json'):
    track_information = load_json('track_information.json')

track_ids = set()
# Listened songs *should* contain liked_songs, but let's be sure.
for record in liked_song_records:
    track_id = record['trackId']
    if track_id in track_ids:
        continue
    if track_id in track_information:
        continue
    track_ids.add(track_id)

for record in listened_song_records:
    track_id = record['trackId']
    if track_id in track_ids:
        continue
    if track_id in track_information:
        continue
    track_ids.add(track_id)

if len(track_ids) > 0:
    print(f'Found {len(track_ids)} unique songs that need to be queried')
    # Track information has all track data, fixing artist name discrepancy
    track_information.update(client.get_track_information(list(track_ids)).items())
    save_json('track_information.json', track_information)
print('Loaded Track Information')

artist_info = {}
if json_exists('artist_info.json'):
    artist_info = load_json('artist_info.json')
print('Getting Artist Information')
artist_ids = set()
for track in track_information.values():
    for artist in track['artists']:
        if artist['id'] in artist_info:
            continue
        artist_ids.add(artist['id'])
print(f'Found {len(artist_ids)} unique artists')
artist_info.update(client.get_artist_info(list(artist_ids)))
save_json('artist_info.json', artist_info)

print('Getting Track Attributes')
track_attributes = client.get_track_attributes(list(track_information.keys()))

