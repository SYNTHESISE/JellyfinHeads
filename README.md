<img width="1895" height="955" alt="image" src="https://github.com/user-attachments/assets/7e652def-43b1-4b2c-9ed9-30b57868b1fb" />




# Jellyfin Heads

This is a little python server that scans your Jellyfin database, and gives you a random character to use in a game of celebrity heads. As this is based on your own Jellyfin library, this is intended to be used with the people who use your Jellyfin server and as such, the characters generated should be pretty guessable even if most are really obscure.

No internet connection necessary, no pulling data from other sources. This runs entirely locally, with only the data that jellyfin has already fetched.
Tested on linux with python 3.14.6 and jellyfin server 10.11.11

# Requirements
[Jellyfin](https://github.com/jellyfin/jellyfin)

[python3](https://www.python.org/)

# How to use
If running on linux with a standard Jellyfin install, you should be able to launch it with

```python3 JellyfinHeads.py```

If you need to specify a different database path, different port, or modify how obscure the characters will be, you can do so with the following optional command line arguments
```
usage: JellyfinHeads.py [-h] [-p PORT] [-P PATH] [-tl TVLIMIT] [-ml MOVIELIMIT]

options:
  -h, --help            show this help message and exit
  -p, --port PORT       Port number to serve the webpage on (default: 5000)
  -P, --path PATH       Path of your Jellyfin database file (default: ~/.var/app/org.jellyfin.JellyfinServer/data/jellyfin/data/jellyfin.db)
  -tl, --tvlimit TVLIMIT
                        Max list order for TV characters (default: 8)
  -ml, --movielimit MOVIELIMIT
                        Max list order for Movie characters (default: 5)
```
Note: when modifying ```tvlimit``` or ```movielimit```, use a lower number for fewer, but more guessable characters, or a higher number to include more obscure characters

Then open a web browser and navigate to your servers IP address on port 5000 (by default).
