<img width="1915" height="871" alt="image" src="https://github.com/user-attachments/assets/f02e3e46-fe44-4dd5-b077-089fd4a8552c" />

# Jellyfin Celebrity Heads

This is a small little python server that scans your Jellyfin database, and gives you a random character to use in a game of celebrity heads. As this is based on your own Jellyfin library, this is intended to be used with the people who use your Jellyfin server and as such, the characters generated should be pretty guessable even if most are really obscure.

I've also added a filter to limit character selection to either TV or Movies.

# How to use
download this to a location of your choosing on your Jellyfin server. Ensure the path to your Jellyfin database is accurate and then run it with 
>python3 JellyfinHeads.py

Then open a web browser and navigate to your servers IP address on port 5000
