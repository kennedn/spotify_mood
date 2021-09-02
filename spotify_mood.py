#!/usr/bin/env python3.9

import pickle
import time
import argparse
from os.path import isfile
from spotipy.oauth2 import SpotifyOAuth
import spotipy


scope = 'user-library-read,playlist-modify-private,playlist-modify-public'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))


# Generate a database of liked tracks that includes genre information
def generate_genre_db():
    items = [None]
    ids = {}
    offset = 0

    # Retrieve each liked track and store related information as a dictionary entry
    # Endpoint has a hard limit of 50 results per call, so use offset variable to adjust until we get no results
    while len(items) > 0:
        items = sp.current_user_saved_tracks(limit=50, offset=offset)['items']
        offset += 50

        for item in items:
            artist = item['track']['artists'][0]
            album = item['track']['album']
            track = item['track']
            ids[track['id']] = {'name': track['name'],
                                'artist': artist['name'],
                                'artist_id': artist['id'],
                                'album': album['name'],
                                'album_id': album['id']}

    if len(ids) == 0:
        print("No tracks were retrieved, exiting")
        exit(1)

    # Get unique list of artist ids from liked tracks
    artist_ids = list(set([t['artist_id'] for t in ids.values()]))

    # Retrieve genre information from each artist
    # Endpoint only accepts up to 50 id's per call, chunk requests to compensate
    chunk_size = 50
    for i in range(0, len(artist_ids), chunk_size):
        artists = sp.artists(artist_ids[i:i + chunk_size]).get('artists')
        for artist in artists:
            genres = artist['genres']
            # genre information is stored against artist, so get a list of tracks tied to a given artist
            key_list = [k for (k, v) in ids.items() if v['artist_id'] == artist['id']]
            for k in key_list:
                # Append genre information to each track, default to 'none' if no genre information is present
                ids[k]['genres'] = genres if len(genres) > 0 else ['none']
    return ids


# Search each tracks genres list for a given value
def search_genres(db, value):
    return [k for (k, v) in db.items() if any(value in g for g in v['genres'])]


# Search for a value against a specific track key
def search_key(db, key, value):
    return [k for (k, v) in db.items() if value.lower() in v[key].lower()]


# Generate unique list of genres from tracks
def list_genres(db):
    return sorted(list(set(g for v in db.values() for g in v['genres'])))


def pretty_print(db, keys):
    for key in keys:
        track = db[key]
        print(track['name'])
        print(f"\tartist: {track['artist']}")
        print(f"\talbum: {track['album']}")
        print(f"\tgenres: {track['genres']}")


# Create a playlist and fill it with passed keys (track ids)
def create_playlist(keys, name=None, description=''):
    # Generate a name based on current time if none was provided
    if name is None:
        t = time.localtime()
        name = time.strftime('%d-%b-%Y_%H%M%S', t)

    # Create playlist
    playlist_id = sp.user_playlist_create(sp.me()['id'], name=name, description=description)['id']

    # Modify keys to expected uri format for endpoint
    keys = [f'spotify:track:{key}' for key in keys]

    # Endpoint only accepts up to 100 tracks per call, chunk requests to compensate
    chunk_size = 100
    for i in range(0, len(keys), chunk_size):
        sp.playlist_add_items(playlist_id, keys[i:i + chunk_size])

    print(f"Added {len(keys)} items to playlist '{name}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='search spotify liked songs based on genre')
    parser.add_argument('-s', '--search', type=str, metavar='term', nargs='?', const=False, default=None,
                        help='search genres for a term')
    parser.add_argument('-k', '--key-search', type=str, metavar=('key', 'term'), nargs='*', default=None,
                        help='search a specific key for a term')
    parser.add_argument('-l', '--list', action="store_true",
                        help='list unique genres present in liked songs')
    parser.add_argument('-c', '--create-playlist', metavar='name', nargs='?', const=False, default=None,
                        help='create a playlist')
    parser.add_argument('-f', '--force-refresh', action="store_true",
                        help='generate fresh database from spotify (delete cache)')

    args = parser.parse_args()

    # Load / Store track database to disk where possible for faster retrieval
    genre_db = None
    if isfile('.spotify_mood.pickle') and not args.force_refresh:
        with open('.spotify_mood.pickle', 'rb') as file:
            genre_db = pickle.load(file)
    if genre_db is None:
        genre_db = generate_genre_db()
        print("Generated new database")
        with open('.spotify_mood.pickle', 'wb') as file:
            pickle.dump(genre_db, file, protocol=pickle.HIGHEST_PROTOCOL)

    # Ensure a search is passed with create_playlist
    if args.create_playlist is not None and (args.search is None and not args.key_search):
        parser.error("A search (-s, -k) needs passed with -c to create playlist")

    # Ensure only one list / search argument is passed
    primary_args = [args.search, args.key_search]
    primary_count = len([i for i in primary_args if i is not None]) + args.list
    if primary_count != 1:
        if primary_count > 1:
            parser.error("search(-s), key-search(-k) and list(-l) cannot be used together")
        elif not args.force_refresh:
            parser.print_usage()

    if args.list:
        for i in list_genres(genre_db):
            print(i)
    elif args.search is not None:
        found_keys = search_genres(genre_db, args.search) if args.search else genre_db.keys()
        pretty_print(genre_db, found_keys)
        if args.create_playlist is not None:
            create_playlist(found_keys, name=args.create_playlist if args.create_playlist else None)
        else:
            print(f"\nFound {len(found_keys)} songs")
    elif args.key_search is not None:
        # Extract a list of keys, excluding genres as it is a list so does not function with search_key()
        valid_keys = list(list(genre_db.values())[0].keys())[:-1]

        if len(args.key_search) == 2:
            if args.key_search[0] not in valid_keys:
                parser.error(f"Passed key must be in {valid_keys}")

            found_keys = search_key(genre_db, args.key_search[0], args.key_search[1])
            pretty_print(genre_db, found_keys)
            if args.create_playlist is not None:
                create_playlist(found_keys, name=args.create_playlist if args.create_playlist else None)
            else:
                print(f"\nFound {len(found_keys)} songs")

        elif len(args.key_search) == 0:
            for key in valid_keys:
                print(key)
        else:
            parser.error("Must supply 0 or 2 parameters with -k")
