import datetime
import json
from time import time, time_ns, sleep
from os import listdir, makedirs
from os.path import exists, join
import requests
import pprint
import os

from spotipy_client import SpotipyClient


def delay_time(goal=3600, step=60):
    start_time = time()

    print(f'Sleeping for {goal}s')
    last = ''
    while (duration := time() - start_time) < goal:
        next = f'\t{round(duration, 1)} / {goal}s'
        print('\b' * len(last) + next, end='')
        last = next
        sleep(min(goal - duration, step))
    print('\b' * len(last) + f'\t{goal} / {goal}')


def save_json(filename, data):
    with open(join('data', filename), 'w', encoding='utf-8') as f:
        json.dump(data, f)


client = SpotipyClient()

if not exists('data/listened'):
    makedirs('data/listened')

if __name__ == "__main__":
    print('Getting Listened Every Hour')
    while True:
        print('Getting Listened')

        next_file = max([int(x[len('songs_update'):-5]) for x in listdir('data/listened') if x.startswith('songs_update')] + [-1]) + 1
        listened_songs = client.get_recent_songs()
        save_json(f'listened/songs_update{next_file}.json', listened_songs)

        current_time = time() % 3600
        seconds_til_hour = 3600 - (int(current_time / 60) * 60 + int(current_time % 60))
        print(f'{seconds_til_hour}s Until the top of the hour')
        delay_time(seconds_til_hour, 60)


