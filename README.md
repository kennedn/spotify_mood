# spotify_mood

A CLI tool for searching liked songs based on genre.

Has the ability to create playlist's based on genre searches.

```bash
usage: spotify_mood.py [-h] [-s [term]] [-k [key [term ...]]] [-l] [-c [name]]
                       [-f]

search spotify liked songs based on genre

optional arguments:
  -h, --help            show this help message and exit
  -s [term], --search [term]
                        search genres for a term
  -k [key [term ...]], --key-search [key [term ...]]
                        search a specific key for a term
  -l, --list            list unique genres present in liked songs
  -c [name], --create-playlist [name]
                        create a playlist
  -f, --force-refresh   generate fresh database from spotify (delete cache)
```


