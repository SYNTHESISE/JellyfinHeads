import sqlite3
import random
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote, urlparse, parse_qs
import socket
from pathlib import Path


#-------------CHANGE BELOW VALUES IF REQUIRED------------------------------------------------------------
PORT = 5000
JELLYFIN_DB = Path("~/.var/app/org.jellyfin.JellyfinServer/data/jellyfin/data/jellyfin.db").expanduser()
#--------------------------------------------------------------------------------------------------------


TV_QUERY = """
WITH CharacterAppearances AS (
    SELECT
        series.Id AS SeriesId,
        series.Name AS SeriesName,
        p.Name AS Performer,
        pbim.Role AS Character,
        COUNT(DISTINCT bi.Id) AS EpisodeCount,
		bi.Genres
    FROM BaseItems bi
    JOIN PeopleBaseItemMap pbim
        ON pbim.ItemId = bi.Id
    JOIN Peoples p
        ON p.Id = pbim.PeopleId
    JOIN BaseItems series
        ON series.Id = bi.SeriesId
    WHERE pbim.Role IS NOT NULL
      AND pbim.Role <> ''
	  AND lower(pbim.Role) not in ('producer', 'writer', 'director', 'himself', 'herself', 'self')
    GROUP BY
        series.Id,
        series.Name,
        p.Name,
        pbim.Role
),
SeriesEpisodeCounts AS (
    SELECT
        SeriesId,
        COUNT(*) AS TotalEpisodes
    FROM BaseItems
    WHERE SeriesId IS NOT NULL
    GROUP BY SeriesId
)
SELECT DISTINCT
    ca.SeriesName AS Title,
    ca.Performer,
    ca.Character,
    pii.Path AS ImagePath,
	pii2.Path AS PosterPath,
	ca.Genres AS Genres
FROM CharacterAppearances ca
JOIN SeriesEpisodeCounts sec
    ON sec.SeriesId = ca.SeriesId
JOIN Peoples p
    ON p.Name = ca.Performer
LEFT JOIN BaseItems personItem
    ON personItem.Name = p.Name
LEFT JOIN BaseItemImageInfos pii
    ON pii.ItemId = personItem.Id
LEFT JOIN BaseItemImageInfos pii2
    ON pii2.ItemId = ca.SeriesId
WHERE CAST(ca.EpisodeCount AS FLOAT) / sec.TotalEpisodes >= 0.30
  AND pii2.ImageType = 0
  AND pii.Path IS NOT NULL
  AND pii2.Path IS NOT NULL;
"""

MOVIE_QUERY="""
SELECT DISTINCT
    bi.Name AS Title,
    p.Name AS Performer,
    pbim.Role AS Character,
    pii.Path AS ImagePath,
	pii2.Path AS PosterPath,
	bi.Genres AS Genres
FROM BaseItems bi
JOIN PeopleBaseItemMap pbim
    ON pbim.ItemId = bi.Id
JOIN Peoples p
    ON p.Id = pbim.PeopleId
LEFT JOIN BaseItems personItem
    ON personItem.Name = p.Name
LEFT JOIN BaseItemImageInfos pii
    ON pii.ItemId = personItem.Id
LEFT JOIN BaseItemImageInfos pii2
	ON pii2.ItemId = pbim.ItemId
WHERE bi.SeriesId IS NULL
  AND bi.UnratedType <> 'Series'
  AND pbim.Role IS NOT NULL
  AND pbim.Role <> ''
  AND lower(pbim.Role) not in ('producer', 'writer', 'director', 'himself', 'herself', 'self')
  AND pii2.ImageType = 0
  AND pii.Path IS NOT NULL
  AND pii2.Path IS NOT NULL;
"""


def loadCharacters(query):
    conn = sqlite3.connect(JELLYFIN_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(query).fetchall()
    conn.close()
    return rows

def getAllGenres(rows):
    genres = set()
    for r in rows:
        for g in r["Genres"].split("|"):
            if g != "":
                genres.add(g)

    sortedList = sorted(genres)
    sortedList.insert(0, "All")
    return sortedList

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path.startswith("/image/"):

            imagePath = unquote(self.path[len("/image/"):])
            if os.path.exists(imagePath):
                self.send_response(200)

                ext = os.path.splitext(imagePath)[1].lower()

                content_types = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".webp": "image/webp"
                }

                self.send_header("Content-Type", content_types.get(ext, "application/octet-stream"))
                self.end_headers()

                with open(imagePath, "rb") as i:
                    self.wfile.write(i.read())

                return

            self.send_error(404)
            return

        parsedPath = urlparse(self.path)
        params = parse_qs(parsedPath.query)

        includeTV = "tv" in params or parsedPath.query == ""
        includeMovies = "movies" in params or parsedPath.query == ""
        selectGenre = "genre" in params

        if includeTV and includeMovies:
            rows = ALL_ROWS
            genreRows = ALL_GENRES
        elif includeTV:
            rows = TV_ROWS
            genreRows = TV_GENRES
        elif includeMovies:
            rows = MOVIE_ROWS
            genreRows = MOVIE_GENRES
        else:
            rows = []
            genreRows = []


        genre = "All"
        if selectGenre and "All" not in params["genre"] and params["genre"][0] in genreRows:
            character = random.choice(rows) if rows else None
            genre = params["genre"]

            while genre[0] not in character["Genres"]:
                character = random.choice(rows) if rows else None
        else:
            character = random.choice(rows) if rows else None

        genreOptionsHTML = ""
        for g in ALL_GENRES:
            genreOptionsHTML = genreOptionsHTML + f"<option value=\"{g}\"{" selected" if g in genre else ""}>{g}</option>"


        if character:
            print(f"""
                character: {character["Character"]}
                Title: {character["Title"]}
                Performer: {character["Performer"]}
                Genres: {character["Genres"]}
            """)

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Random Character</title>
                <style>
                    body {{
                        background:#111;
                        color:#aaa;
                        text-align:center;
                        font-family:Arial;
                        padding-top:20px;
                    }}

                    img {{
                        max-height:600px;
                        max-width:400px;
                        border-radius:15px;
                    }}

                    .character {{
                        font-size:40px;
                        font-weight:bold;
                        color:white;
                    }}

                    .actor {{
                        margin-top:20px;
                        margin-bottom:10px;
                        font-size:26px;
                    }}

                    .title {{
                        margin-top:10px;
                        font-size:24px;
                        color:#baaba;
                    }}

                    .genre {{
                        margin-top:5px;
                        font-size:18px;
                        color:#baaba;
                    }}

                    button {{
                        margin-top:20px;
                        padding:15px 30px;
                        font-size:20px;
                    }}
                    label {{
                        font-size:20px;
                        margin:0 10px;
                    }}

                    input[type=checkbox] {{
                        transform:scale(1.5);
                        margin-right:8px;
                    }}
                </style>
            </head>

            <body>

            <div class="character">
                {character["Character"]}
            </div>

            <div class="title">
                {character["Title"]}
            </div>

            <div class="genre">
                {" | ".join(character["Genres"].split("|"))}
            </div>

            <div class="actor">
                {character["Performer"]}
            </div>

            <img src="/image/{character["ImagePath"]}">
            <img src="/image/{character["PosterPath"]}">
            <br>

            <form method="GET">

            <label>
                <input
                    type="checkbox"
                    name="tv"
                    value="1"
                    {"checked" if includeTV else ""}
                >
                TV
            </label>

            <label style="margin-left:25px;">
                <input
                    type="checkbox"
                    name="movies"
                    value="1"
                    {"checked" if includeMovies else ""}
                >
                Movies
            </label>

            <br><br>
            <label> Genre:
            <select name="genre" id="genre-select">
            {genreOptionsHTML}
            </select>
            </label>

            <br>

            <button type="submit">
                New Character
            </button>
            <br><br>

            </form>

            </body>
            </html>
            """

        else:
            html = "No characters found. Please ensure your jellyfin database has content loaded."


        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

print("Scanning Database...")

TV_ROWS = loadCharacters(TV_QUERY)
MOVIE_ROWS = loadCharacters(MOVIE_QUERY)
ALL_ROWS = TV_ROWS + MOVIE_ROWS

TV_GENRES = getAllGenres(TV_ROWS)
MOVIE_GENRES = getAllGenres(MOVIE_ROWS)
ALL_GENRES = getAllGenres(ALL_ROWS)

print(f"TV Characters: {len(TV_ROWS)}")
print(f"Movie Characters: {len(MOVIE_ROWS)}")
print(f"Total Characters: {len(ALL_ROWS)}")

#Get local IP address so the user clearly knows how to access this - although might not always be accurate
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
ipAddress = s.getsockname()[0]

print(f"Server running on http://{ipAddress}:{PORT}")

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
