"""Web server: serve the board UI and its JSON API using the standard library.

One responsibility: HTTP transport. It routes requests onto the four webapi
actions and serves the three static files that make up the page. It holds no
board rules (Board) and no API logic (webapi) — only routing, body decoding, and
response writing. Pure standard library: http.server + json, zero dependencies.
"""

import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from kanban import webapi

# ===== Constants =====

# The static page lives beside this module so the server is self-contained and
# finds its own assets with no install step or working-directory assumptions.
STATIC_DIR = Path(__file__).parent / "static"

# Content types for the only three asset kinds the page uses. Listing just these
# keeps the table honest — YAGNI over a full mimetypes registry.
_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}

# Matches the card id in an "/api/cards/<id>..." path. Compiled once at import.
_CARD_ID = re.compile(r"^/api/cards/(\d+)")


# ===== Request handler =====


# Build a handler class bound to one board file. A factory (rather than a module
# global) keeps the file path explicit and lets tests run isolated servers.
def _build_handler(board_file: str) -> type:
    class KanbanHandler(BaseHTTPRequestHandler):
        """Route one HTTP request to a webapi action or a static file. The board
        lives entirely in the file; this object is recreated per request and
        carries no state of its own."""

        # ----- response helpers -----

        # Write a JSON response in one place so every route stays a single action
        # call plus this send — no repeated header/encode boilerplate.
        def _send_json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        # Decode a JSON request body into a dict. A missing or malformed body
        # becomes {} so action-level validation, not parsing, owns the error.
        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            if not length:
                return {}
            try:
                return json.loads(self.rfile.read(length))
            except json.JSONDecodeError:
                return {}

        # ----- routing -----

        def do_GET(self) -> None:
            if self.path == "/api/board":
                self._send_json(*webapi.get_board(board_file))
            else:
                self._serve_static(self.path)

        def do_POST(self) -> None:
            if self.path == "/api/cards":
                self._send_json(*webapi.add_card(board_file, self._read_json()))
                return
            match = _CARD_ID.match(self.path)
            if match and self.path.endswith("/move"):
                card_id = int(match.group(1))
                self._send_json(*webapi.move_card(board_file, card_id, self._read_json()))
                return
            self._send_json(404, {"error": "not found"})

        def do_DELETE(self) -> None:
            match = _CARD_ID.match(self.path)
            # Require an exact "/api/cards/<id>" so a stray suffix can't delete.
            if match and self.path == f"/api/cards/{match.group(1)}":
                self._send_json(*webapi.remove_card(board_file, int(match.group(1))))
                return
            self._send_json(404, {"error": "not found"})

        # ----- static files -----

        # Serve a file from STATIC_DIR, defaulting "/" to index.html. The resolved
        # target must sit inside STATIC_DIR so a crafted "../" URL can't escape the
        # folder and read arbitrary files.
        def _serve_static(self, url_path: str) -> None:
            name = "index.html" if url_path in ("/", "") else url_path.lstrip("/")
            target = (STATIC_DIR / name).resolve()
            if STATIC_DIR.resolve() not in target.parents or not target.is_file():
                self.send_error(404, "Not found")
                return
            body = target.read_bytes()
            content_type = _CONTENT_TYPES.get(target.suffix, "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        # Silence the default per-request stderr logging; the serve banner is the
        # only output a tidy showcase run should print.
        def log_message(self, *args) -> None:
            pass

    return KanbanHandler


# ===== Server entry =====


# Build an HTTPServer bound to localhost. Returned unstarted so callers (the CLI,
# tests) choose when to serve and can shut it down cleanly.
def create_server(port: int, board_file: str) -> HTTPServer:
    return HTTPServer(("127.0.0.1", port), _build_handler(board_file))


# Start serving and block, printing the URL so the user knows where to look.
# Ctrl-C raises KeyboardInterrupt, which the CLI translates into a clean exit.
def serve(port: int, board_file: str) -> None:
    server = create_server(port, board_file)
    print(
        f"Kanban board UI: http://127.0.0.1:{port}"
        f"  (file: {board_file}, Ctrl-C to stop)"
    )
    server.serve_forever()
