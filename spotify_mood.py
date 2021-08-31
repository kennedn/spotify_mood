#!/usr/bin/env python3

import requests
import pprint
import pickle
import time
import json
import argparse
from os.path import isfile

with open('.spotify_mood.auth', 'r') as file:
  auth_key = file.read().splitlines()[0]

headers = { 'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {0}'.format(auth_key) }

def generate_genre_db(auth):

  url = 'https://api.spotify.com/v1/me/tracks?limit=50&offset={0}'
  items = [None]
  ids = {}
  offset = 0

  while len(items) > 0:
    request = requests.get(url.format(offset), headers=headers)
    if request.status_code >= 400:
      print(f"Could not get liked tracks. RC: {request.status_code}")
      print(request.json())
      return
    items = request.json().get('items')
    for item in items:
      artist = item['track']['artists'][0]
      album = item['track']['album']
      track = item['track']
      ids[track['id']] = { 'name': track['name'], 'artist': artist['name'], 'artist_id': artist['id'], 'album': album['name'], 'album_id': album['id'] }
    offset += 50

  if len(ids) == 0:
    print("No tracks were retrieved, exiting")
    exit(1)

  artist_ids = [ t.get('artist_id') for t in ids.values() ]
  album_genres = {}
  url = 'https://api.spotify.com/v1/artists?ids={0}'
  chunk_size = 50

  for i in range(0, len(artist_ids), chunk_size):
    id_chunk = ','.join(artist_ids[i:i + chunk_size])
    request = requests.get(url.format(id_chunk), headers=headers)
    artists = request.json().get('artists')
    for artist in artists:
      genres = artist['genres']
      key_list = [ k for (k,v) in ids.items() if v['artist_id'] == artist['id'] ]
      for k in key_list:
        ids[k]['genres'] = genres
  return ids
  
 
def search_db(db, value):
  return [ k for (k, v) in db.items() if any(value in g for g in v['genres']) ]

def list_genres(db):
  return list(set(g for v in db.values() for g in v['genres']))

def pretty_print(db, keys):
  for key in keys:
    track = db[key]
    print(track['name'])
    print(f"\tartist: {track['artist']}")
    print(f"\talbum: {track['album']}")
    print(f"\tgenres: {track['genres']}")



def create_playlist(keys, name=None, description=''):
  url = 'https://api.spotify.com/v1/users/kennedn/playlists'
  if name is None:
    t = time.localtime()
    name = time.strftime('%d-%b-%Y_%H%M%S', t)
  request = requests.post(url, headers=headers, data = json.dumps({'name': name, 'description': description, 'public': False}))

  if request.status_code >= 400:
    print(f"Could not create playlist. RC: {request.status_code}")
    return

  playlist_id = request.json()['id']
  url = 'https://api.spotify.com/v1/playlists/{0}/tracks?uris={1}'
  keys = [ f'spotify:track:{key}' for key in keys ]
  chunk_size = 100
  for i in range(0, len(keys), chunk_size):
    key_chunk = ','.join(keys[i:i + chunk_size])
    request = requests.post(url.format(playlist_id, key_chunk), headers=headers)

  if request.status_code >= 400:
    print(f"Could not add items to playlist. RC: {request.status_code}")
    print(request.json())
    return
  else:
    print(f"Added {len(keys)} items to playlist '{name}'")

   
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='search spotify liked songs based on genre')
  parser.add_argument('-s', '--search', type=str, metavar='term', nargs='?', const=False, default=None, help='genre search term')
  parser.add_argument('-c', '--create-playlist', metavar='name', nargs='?', const=False, default=None, help='create a playlist')
  parser.add_argument('-l', '--list', action="store_true", help='list unique genres present in liked songs')
  parser.add_argument('-f', '--force-refresh', action="store_true", help='generate fresh database from spotify (delete cache)')

  args = parser.parse_args()

  genre_db = None
  if isfile('.spotify_mood.pickle') and not args.force_refresh:
    with open('.spotify_mood.pickle', 'rb') as file:
      genre_db = pickle.load(file)
  else:
    genre_db = generate_genre_db(auth_key)
    with open('.spotify_mood.pickle', 'wb') as file:
      pickle.dump(genre_db, file, protocol=pickle.HIGHEST_PROTOCOL)

  if args.list:
    for i in list_genres(genre_db):
      print(i)
  elif args.create_playlist is not None:
    if args.search is None:
      print('search term required to create playlist')
      args.print_usage()
      exit(1)
    playlist_name = args.create_playlist if args.create_playlist else None
    create_playlist(search_db(genre_db, args.search),name=playlist_name)
  elif args.search is not None:
    pretty_print(genre_db, search_db(genre_db, args.search)) if args.search else pretty_print(genre_db, genre_db.keys())



  
  
  
  

