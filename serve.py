"""Preview the built site at http://localhost:4173 (run build.py first).

    python3 serve.py

Pages are sent with "no-store" so the browser always shows the latest build.
"""
import functools
import http.server
from pathlib import Path

PORT = 4173
SITE = Path(__file__).parent / "_site"


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    handler = functools.partial(NoCacheHandler, directory=str(SITE))
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler) as server:
        print(f"Serving {SITE} at http://localhost:{PORT}")
        server.serve_forever()
