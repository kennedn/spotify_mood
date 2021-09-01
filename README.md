# spotify_mood

A CLI tool for searching liked songs based on genre.

Has the ability to create playlist's based on genre searches.

```bash
usage: spotify_mood.py [-h] [-s term] [-c [name]] [-l] [-f]

search spotify liked songs based on genre

optional arguments:
  -h, --help            show this help message and exit
  -s term, --search term
                        genre search term
  -c [name], --create-playlist [name]
                        create a playlist
  -l, --list            list unique genres present in liked songs
  -f, --force-refresh   generate fresh database from spotify (delete cache)
```


