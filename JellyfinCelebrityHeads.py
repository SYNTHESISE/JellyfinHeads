import sqlite3
import random
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote, urlparse, parse_qs
import socket
from pathlib import Path


# CHANGE THIS IF NECESSARY
tildePath = Path("~/.var/app/org.jellyfin.JellyfinServer/data/jellyfin/data/jellyfin.db")
JELLYFIN_DB = tilde_path.expanduser()


TV_QUERY = """
WITH CharacterAppearances AS (
    SELECT
        series.Id AS SeriesId,
        series.Name AS SeriesName,
        p.Name AS Performer,
        pbim.Role AS Character,
        COUNT(DISTINCT bi.Id) AS EpisodeCount
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
    pii.Path AS ImagePath
FROM CharacterAppearances ca
JOIN SeriesEpisodeCounts sec
    ON sec.SeriesId = ca.SeriesId
JOIN Peoples p
    ON p.Name = ca.Performer
LEFT JOIN BaseItems personItem
    ON personItem.Name = p.Name
LEFT JOIN BaseItemImageInfos pii
    ON pii.ItemId = personItem.Id
WHERE CAST(ca.EpisodeCount AS FLOAT) / sec.TotalEpisodes >= 0.30
  AND pii.Path IS NOT NULL;
"""

MOVIE_QUERY="""
SELECT DISTINCT
    bi.Name AS Title,
    p.Name AS Performer,
    pbim.Role AS Character,
    pii.Path AS ImagePath
FROM BaseItems bi
JOIN PeopleBaseItemMap pbim
    ON pbim.ItemId = bi.Id
JOIN Peoples p
    ON p.Id = pbim.PeopleId
LEFT JOIN BaseItems personItem
    ON personItem.Name = p.Name
LEFT JOIN BaseItemImageInfos pii
    ON pii.ItemId = personItem.Id
WHERE bi.SeriesId IS NULL
  AND pbim.Role IS NOT NULL
  AND pbim.Role <> ''
  AND lower(pbim.Role) not in ('producer', 'writer', 'director', 'himself', 'herself', 'self')
  AND pii.Path IS NOT NULL;
"""


def loadCharacters(query):
    conn = sqlite3.connect(JELLYFIN_DB)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(query).fetchall()

    conn.close()

    return rows



class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path.startswith("/image/"):
            image_path = unquote(self.path[len("/image/"):])

            if os.path.exists(image_path):
                self.send_response(200)

                ext = os.path.splitext(image_path)[1].lower()

                content_types = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".webp": "image/webp"
                }

                self.send_header(
                    "Content-Type",
                    content_types.get(ext, "application/octet-stream")
                )

                self.end_headers()

                with open(image_path, "rb") as f:
                    self.wfile.write(f.read())

                return

            self.send_error(404)
            return

        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        include_tv = "tv" in params
        include_movies = "movies" in params

        # First visit defaults to both
        if parsed.query == "":
            include_tv = True
            include_movies = True

        if include_tv and include_movies:
            rows = ALL_ROWS
        elif include_tv:
            rows = TV_ROWS
        elif include_movies:
            rows = MOVIE_ROWS
        else:
            rows = []

        character = random.choice(rows) if rows else None

        if character:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Random Character</title>
                <style>
                    body {{
                        background:#111;
                        color:white;
                        text-align:center;
                        font-family:Arial;
                        padding-top:40px;
                    }}

                    img {{
                        max-height:600px;
                        max-width:400px;
                        border-radius:15px;
                    }}

                    .character {{
                        font-size:36px;
                        font-weight:bold;
                    }}

                    .actor {{
                        font-size:22px;
                        color:#aaa;
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

            <div class="actor">
                {character["Performer"]}
            </div>

            <img src="/image/{character["ImagePath"]}">

            <br>

            <form method="GET">

            <label>
                <input
                    type="checkbox"
                    name="tv"
                    value="1"
                    {"checked" if include_tv else ""}
                >
                TV
            </label>

            <label style="margin-left:25px;">
                <input
                    type="checkbox"
                    name="movies"
                    value="1"
                    {"checked" if include_movies else ""}
                >
                Movies
            </label>

            <br><br>

            <button type="submit">
                New Character
            </button>

            </form>

            </body>
            </html>
            """
        else:
            html = "<h1>No characters found</h1>"

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


server = HTTPServer(("0.0.0.0", 5000), Handler)
TV_ROWS = loadCharacters(TV_QUERY)
MOVIE_ROWS = loadCharacters(MOVIE_QUERY)
ALL_ROWS = TV_ROWS + MOVIE_ROWS

print(f"TV: {len(TV_ROWS)}")
print(f"Movies: {len(MOVIE_ROWS)}")
print(f"Total: {len(ALL_ROWS)}")

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
ipAddress = s.getsockname()[0]

print(f"Server running on http://{ipAddress}:5000")
server.serve_forever()
