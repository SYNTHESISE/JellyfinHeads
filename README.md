<img width="1895" height="955" alt="image" src="https://github.com/user-attachments/assets/7e652def-43b1-4b2c-9ed9-30b57868b1fb" />




# Jellyfin Heads

This is a little python server that scans your Jellyfin database, and gives you a random character to use in a game of celebrity heads. As this is based on your own Jellyfin library, this is intended to be used with the people who use your Jellyfin server and as such, the characters generated should be pretty guessable even if most are really obscure.

No internet connection necessary, no pulling data from other sources. This runs entirely locally, with only the data that jellyfin has already fetched.
Tested on linux with jellyfin server 10.11.11

# Requirements
[Jellyfin](https://github.com/jellyfin/jellyfin)

[python3](https://www.python.org/)

# How to use
Ensure the path to your Jellyfin database within JellyfinHeads.py is accurate and then run the server with 
>python3 JellyfinHeads.py

Then open a web browser and navigate to your servers IP address on port 5000.
