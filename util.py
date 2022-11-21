import json
from os import listdir, makedirs, remove
from os.path import exists, join, split


# https://stackoverflow.com/questions/39047624/is-there-an-easy-way-to-estimate-size-of-a-json-object
# File-like object, throws away everything you write to it but keeps track of the size.
class MeterFile:
    def __init__(self, size=0):
        self.size = size

    def write(self, string):
        self.size += len(string)


# Calculates the JSON-encoded size of an object without storing it.
def json_size(obj, *args, **kwargs):
    mf = MeterFile()
    json.dump(obj, mf, *args, **kwargs)
    return mf.size


def load_json(filename):
    with open(join('data', filename), 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            raise Exception(f'Failed to load json {filename}')


def save_json(filename, data):
    with open(join('data', filename), 'w', encoding='utf-8') as f:
        try:
            json.dump(data, f)
        except Exception:
            raise Exception(f'Failed to load json {filename}')


def save_chunked_json(base_filename, data):
    directory, basename = split(base_filename)
    if basename.endswith('.json'):
        basename = basename[:-5]
    if not exists(join('data', directory)):
        makedirs(join('data', directory))

    keys = list(data.keys())
    length = len(keys)
    chunk_size = length // 2

    chunk = {k: data[k] for k in keys[:chunk_size]}
    while json_size(chunk) > 95 * 1024 * 1024:  # 75 MB
        chunk_size = chunk_size // 2
        chunk = {k: data[k] for k in keys[:chunk_size]}

    if json_exists(join(directory, basename + '0.json')):
        for file in [x for x in listdir(join('data', directory)) if x.startswith(basename)]:
            remove(join('data', directory, file))

    save_json(join(directory, basename + '0.json'), chunk)
    file_index = 1
    for ix in range(chunk_size, length, chunk_size):
        chunk = {k: data[k] for k in keys[ix:ix + chunk_size]}
        save_json(join(directory, basename + f'{file_index}.json'), chunk)
        file_index += 1


def load_chunked_json(base_filename):
    directory, basename = split(base_filename)
    if basename.endswith('.json'):
        basename = basename[:-5]
    files = [x for x in listdir(join('data', directory)) if x.startswith(basename)]
    full_data = {}
    for file in files:
        for k, v in load_json(join(directory, file)).items():
            full_data[k] = v
    print(f'Loaded {len(full_data.keys())} items')
    return full_data


def json_exists(filename):
    return exists(join('data', filename))


def chunked_json_exists(base_filename):
    directory, basename = split(base_filename)
    if basename.endswith('.json'):
        basename = basename[:-5]
    files = [x for x in listdir(join('data', directory)) if x.startswith(basename)]
    return len(files) > 0
