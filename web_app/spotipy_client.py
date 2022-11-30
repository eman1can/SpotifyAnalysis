import urllib.parse
from os import listdir
from os.path import join
from datetime import datetime
import numpy as np

import spotipy
import spotipy.util as util
from spotipy import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from util import chunked_json_exists, load_chunked_json, load_json, json_exists, save_chunked_json, save_json

SPOTIPY_CLIENT_ID = '5f37f812086545ca9ad3d0a72cd78fe8'
SPOTIPY_CLIENT_SECRET = 'e68639fecea745e29a1c45798418db8f'


class SpotipyClient:
    def __init__(self):
        scope = 'user-top-read,user-library-read,user-read-recently-played'
        oauth = SpotifyOAuth(scope=scope, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri='http://127.0.0.1:9090')
        self._sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET), auth_manager=oauth)

    def _parse_release_date(self, album):
        precision = album['release_date_precision']
        if precision == 'year':
            return datetime.strptime(album['release_date'], '%Y')
        elif precision == 'month':
            return datetime.strptime(album['release_date'], '%Y-%m')
        elif precision == 'day':
            return datetime.strptime(album['release_date'], '%Y-%m-%d')
        else:
            print('Unknown precision', precision)
            return datetime.now()

    def _resolve_republished(self, tracks, played_date):
        dates = [self._parse_release_date(track['album']) for track in tracks]
        pre_played_dates = []
        for ix, date in enumerate(dates):
            if date > played_date:
                continue
            pre_played_dates.append(ix)
        if len(pre_played_dates) == 1:
            return tracks[pre_played_dates[0]]['id']
        return tracks[np.argmax([track['popularity'] for track in tracks])]['id']

    def _clean_name(self, name):
        name = name.lower()
        name = name.replace('\'', '')
        name = name.replace('\u2019', '')
        name = name.replace('\u2018', '')
        name = name.replace('?', '')
        if '(' in name:
            name = name[:name.index('(')].strip()
        if '-' in name:
            name = name[:name.index('-')].strip()
        return name.title()

    def _parse_history(self, played):
        # endTime
        # artistName
        # trackName
        # trackId
        # msPlayed

        ids = {}
        to_remove = []
        if json_exists('track_ids.json'):
            ids = load_json('track_ids.json')

        removed_songs = load_json('removed.json')

        print(f'{0:6} / {len(played):6}', end='')
        for ix, record in enumerate(played):
            print('\b' * 15 + f'{ix:6} / {len(played):6}', end='')

            if record['artistName'] in removed_songs and record['trackName'] in removed_songs[record['artistName']]:
                print('\nSkipping', record['trackName'], 'by', record['artistName'] + '; Removed.')
                to_remove.append(ix)
                continue

            key = record['trackName'] + '_' + record['artistName']
            if 'trackId' in record.keys():
                if key not in ids:
                    ids[key] = record['trackId']
                    save_json('track_ids.json', ids)
                continue

            if key in ids.keys():
                record['trackId'] = ids[key]
                continue

            query = 'track:' + self._clean_name(record['trackName']) + ', artist:' + self._clean_name(record['artistName'])
            tracks = self._sp.search(query, type='track')['tracks']['items']

            if len(tracks) > 1:
                played_date = datetime.strptime(record['endTime'], '%Y-%m-%d %H:%M')
                filtered_tracks = [track for track in tracks if (self._clean_name(track['name']) == self._clean_name(record['trackName']) and self._clean_name(track['artists'][0]['name']) == self._clean_name(record['artistName']))]
                album_types = [track['album']['album_type'] for track in tracks]
                if len(set(album_types)) > 1 and 'compilation' in album_types:
                    filtered_tracks = [track for track in filtered_tracks if track['album']['album_type'] != 'compilation']
                if len(filtered_tracks) == 1:
                    ids[key] = record['trackId'] = filtered_tracks[0]['id']
                    save_json('track_ids.json', ids)
                    continue
                if len(filtered_tracks) == 0:
                    print('\nAll Filtered Tracks Skipped')
                    for track in tracks:
                        print(track['album']['name'])
                        print(track['album']['album_type'])
                        print(track['name'])
                    print('Skipping track', record['trackName'], 'by', record['artistName'])
                    to_remove.append(ix)
                    continue
                ids[key] = record['trackId'] = self._resolve_republished(filtered_tracks, played_date)
                save_json('track_ids.json', ids)
                continue
            if len(tracks) == 0:
                print('\nCan\'t find track', record['trackName'], 'by', record['artistName'])
                to_remove.append(ix)
                continue
            ids[key] = record['trackId'] = tracks[0]['id']
            save_json('track_ids.json', ids)
        save_json('track_ids.json', ids)
        for ix in reversed(to_remove):
            played.pop(ix)

        return played

    def _get_past_history(self):
        if json_exists('past_history.json'):
            return load_json('past_history.json')
        history_files = [x for x in listdir(join('data', 'history')) if x.startswith('endsong')]
        played = []
        for file in history_files:
            for song in load_json(join('history', file)):
                played_at = datetime.strptime(song['ts'], '%Y-%m-%dT%H:%M:%SZ')
                if song['master_metadata_album_artist_name'] is None:
                    continue
                played.append({
                    'endTime': played_at.strftime("%Y-%m-%d %H:%M"),
                    'artistName': song['master_metadata_album_artist_name'],
                    'trackName': song['master_metadata_track_name'],
                    'msPlayed': song['ms_played'],
                    'trackId': song['spotify_track_uri'][len('spotify:track:'):]
                })
        return self._parse_history(played)

    def _get_history(self):
        history_files = [x for x in listdir('data') if x.startswith('StreamingHistory')]
        played = []
        played_keys = set()
        for file in history_files:
            for song in load_json(file):
                key = song['trackName'] + '_' + song['endTime']
                if key not in played_keys:
                    played_keys.add(key)
                    played.append(song)
        return self._parse_history(list(played))

    def _get_recent(self):
        recent_files = [x for x in listdir(join('data', 'listened'))]
        played = []
        listened = set()
        for file in recent_files:
            print(f'Loading {file}')
            data = load_json(join('listened', file))

            for song in data['items']:
                key = song['track']['id'] + '_' + song['played_at']
                if key in listened:
                    continue
                listened.add(key)
                played_at = datetime.strptime(song['played_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                played.append({
                    'endTime': played_at.strftime("%Y-%m-%d %H:%M"),
                    'trackName': song['track']['name'],
                    'trackId': song['track']['id'],
                    'artistName': song['track']['artists'][0]['name'],
                    'msPlayed': song['track']['duration_ms']
                })
        return played

    def get_recent_songs(self):
        return self._sp.current_user_recently_played()

    def get_listened_songs(self):
        if json_exists('listened_songs.json'):
            return load_json('listened_songs.json')
        listened_keys = set()
        listened = []

        def add_songs(songs):
            for song in songs:
                key = song['trackId'] + '_' + song['endTime']
                if key not in listened_keys:
                    listened_keys.add(key)
                    listened.append(song)

        add_songs(self._get_past_history())
        add_songs(self._get_history())
        add_songs(self._get_recent())

        save_json('listened_songs.json', list(listened))
        return list(listened)

    def get_liked_songs(self):
        if json_exists('liked_songs.json'):
            return load_json('liked_songs.json')
        tracks = []
        more_songs = True
        offset = 0
        print('Querying liked songs')
        while more_songs:
            songs = self._sp.current_user_saved_tracks(offset=offset)
            for song in songs['items']:
                tracks.append({
                    'added_at': song['added_at'],
                    'trackId': song['track']['id']
                })

            if songs['next'] == None:
                # no more songs in playlist
                more_songs = False
            else:
                # get the next n songs
                offset += songs['limit']
                print('Progress: ' + str(offset) + ' of ' + str(songs['total']))
        save_json('liked_songs.json', tracks)
        return tracks

    def get_track_information(self, track_ids):
        track_info = {}
        print(f'{0:6} / {len(track_ids):6}', end='')
        for ix in range(0, len(track_ids), 50):
            for track in self._sp.tracks(track_ids[ix:ix + 50])['tracks']:
                if track is None:
                    continue
                track_info[track['id']] = track
            print('\b' * 15 + f'{ix:6} / {len(track_ids):6}', end='')
        print('\b' * 15 + f'{len(track_ids):6} / {len(track_ids):6}')
        return track_info

    def get_audio_features(self, track_ids):
        features = {}
        print(f'{0:6} / {len(track_ids):6}', end='')
        for ix in range(0, len(track_ids), 100):
            for track in self._sp.audio_features(track_ids[ix:ix + 100]):
                if track is None:
                    continue
                features[track['id']] = track
            print('\b' * 15 + f'{ix:6} / {len(track_ids):6}', end='')
        print('\b' * 15 + f'{len(track_ids):6} / {len(track_ids):6}')
        return features

    def get_track_attributes(self, track_ids):
        track_info = {'features': {}, 'analysis': {}}
        if json_exists('internal_audio_features.json'):
            track_info['features'] = load_json('internal_audio_features.json')
        to_query = []
        for track_id in track_ids:
            if track_id in track_info['features']:
                continue
            to_query.append(track_id)
        print('Getting Audio Features')
        if len(to_query) > 0:
            print(f'{0:6} / {len(to_query):6}', end='')
            for ix in range(0, len(to_query), 100):
                for track in self._sp.audio_features(to_query[ix:ix + 100]):
                    if track is None:
                        continue
                    track_info['features'][track['id']] = track
                print('\b' * 15 + f'{ix:6} / {len(to_query):6}', end='')
                save_json('internal_audio_features.json', track_info['features'])
            print('\b' * 15 + f'{len(to_query):6} / {len(to_query):6}')
            # Account for tracks which have no features
            for track_id in track_ids:
                if track_id not in track_info['features']:
                    track_info['features'][track_id] = None
            save_json('internal_audio_features.json', track_info['features'])
        print('Got all Audio Features')
        print('Getting Audio Analysis')
        return track_info
        if chunked_json_exists('audio/analysis.json'):
            track_info['analysis'] = load_chunked_json('audio/analysis.json')
        if len(track_info['analysis'].keys()) < len(track_ids):
            print(f'{0:4} / {len(track_ids):4}', end='')
            for ix, track_id in enumerate(track_ids):
                if track_id in track_info['analysis']:
                    continue
                try:
                    result = self._sp.audio_analysis(track_id)
                except SpotifyException:
                    continue
                if result is None:
                    continue
                track_info['analysis'][track_id] = result
                print('\b' * 11 + f'{ix:4} / {len(track_ids):4}', end='')
                if ix % 125 == 0 and ix != 0:
                    # save_json('internal_audio_analysis_master.json', track_info['analysis'])
                    save_chunked_json('audio/analysis.json', track_info['analysis'])
            print('\b' * 11 + f'{len(track_ids):4} / {len(track_ids):4}')
            # Account for tracks which have no analysis
            for track_id in track_ids:
                if track_id not in track_info['analysis']:
                    track_info['analysis'][track_id] = None
            save_json('internal_audio_analysis.json', track_info['analysis'])
        return track_info

    def get_artist_info(self, artist_ids):
        artist_info = {}
        print(f'{0:4} / {len(artist_ids):4}', end='')
        for ix in range(0, len(artist_ids), 50):
            for artist in self._sp.artists(artist_ids[ix:ix + 50])['artists']:
                if artist is None:
                    continue
                artist_info[artist['id']] = artist
            print('\b' * 11 + f'{ix:4} / {len(artist_ids):4}', end='')
        print('\b' * 11 + f'{len(artist_ids):4} / {len(artist_ids):4}')
        return artist_info
