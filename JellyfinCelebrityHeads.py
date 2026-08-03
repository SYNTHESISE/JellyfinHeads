import sqlite3
import random
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote

JELLYFIN_DB = "ENTER THE PATH TO YOUR JELLYFIN DB HERE"  # change this

QUERY = """
SELECT
    series.Name AS Title,
    CASE
        WHEN bi.SeriesId IS NOT NULL THEN 'Series'
        ELSE bi.Type
    END AS MediaType,
    p.Name AS Performer,
    pbim.Role AS Character,
    pii.Path AS ImagePath
FROM BaseItems bi
JOIN PeopleBaseItemMap pbim
    ON pbim.ItemId = bi.Id
JOIN Peoples p
    ON p.Id = pbim.PeopleId
LEFT JOIN BaseItems series
    ON series.Id = COALESCE(bi.SeriesId, bi.Id)
LEFT JOIN BaseItems personItem
    ON personItem.Name = p.Name
LEFT JOIN BaseItemImageInfos pii
    ON pii.ItemId = personItem.Id
WHERE bi.Type IN ('Movie', 'Series', 'MediaBrowser.Controller.Entities.TV.Episode')
  AND pbim.Role IS NOT NULL
  AND pbim.Role <> ''
  AND pii.Path IS NOT NULL
"""

def get_random_character():
    conn = sqlite3.connect(JELLYFIN_DB)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(QUERY).fetchall()
    conn.close()

    if not rows:
        return None

    return random.choice(rows)


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

        character = get_random_character()

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
                </style>
            </head>

            <body>

            <h1>Random Character</h1>

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

            <form>
                <button>New Character</button>
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

print("Server running on http://localhost:5000")
server.serve_forever()
