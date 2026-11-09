"""Local HTTP server with Range support, so downloads run against urllib3's real response API."""

import re
from http.server import BaseHTTPRequestHandler

# Non-repeating within a 1 KB chunk (256 would repeat), so a misplaced chunk changes the bytes.
RANGE_CONTENT = bytes(i % 251 for i in range(5000))


class RangeHandler(BaseHTTPRequestHandler):
    """Serves RANGE_CONTENT at /file with HTTP Range support; anything else is a 404."""

    def do_GET(self):
        if self.path != "/file":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 page not found")
            return
        start, end = map(int, re.match(r"bytes=(\d+)-(\d+)", self.headers["Range"]).groups())
        body = RANGE_CONTENT[start : end + 1]
        self.send_response(206)
        self.send_header("Content-Range", f"bytes {start}-{end}/{len(RANGE_CONTENT)}")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence request logging
        pass
