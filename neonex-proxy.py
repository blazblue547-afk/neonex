#!/usr/bin/env python3
"""NEONEX Search Proxy — forwards requests to Brave Search API from localhost.
   Keeps your API key server-side so it never hits the browser."""

import json, os, sys, gzip, io
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.parse import urlparse, parse_qs, quote
from urllib.error import HTTPError

API_KEY = os.environ.get("BRAVE_API_KEY", "")
# Also try reading from file
_key_file = os.path.join(os.path.dirname(__file__), ".neonex_key")
if not API_KEY and os.path.exists(_key_file):
    with open(_key_file) as f:
        API_KEY = f.read().strip()
PORT = int(os.environ.get("PORT", "8777"))
BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"

class Proxy(BaseHTTPRequestHandler):
    def do_GET(self):
        global API_KEY
        parsed = urlparse(self.path)

        # Serve the HTML file
        if parsed.path == "/" or parsed.path == "/index.html":
            html_path = os.path.join(os.path.dirname(__file__), "NEONEX Search Engine.html")
            if not os.path.exists(html_path):
                html_path = os.path.join(os.getcwd(), "NEONEX Search Engine.html")
            try:
                with open(html_path) as f:
                    html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(html.encode())
            except FileNotFoundError:
                self.send_error(404, "NEONEX HTML file not found")
            return

        # API key set/check
        if parsed.path == "/key":
            params = parse_qs(parsed.query)
            if "set" in params:
                raw = params["set"][0]
                # Support base64-encoded keys
                import base64 as _b64
                try:
                    API_KEY = _b64.b64decode(raw).decode()
                except Exception:
                    API_KEY = raw
                self.send_json({"status": "ok", "has_key": True})
                return
            if "setb64" in params:
                import base64 as _b64
                API_KEY = _b64.b64decode(params["setb64"][0]).decode()
                self.send_json({"status": "ok", "has_key": True})
                return
            self.send_json({"has_key": bool(API_KEY)})
            return

        # Search proxy
        if parsed.path == "/search":
            if not API_KEY:
                self.send_json({"error": "No API key configured. Set BRAVE_API_KEY env var or POST /key?set=YOUR_KEY"}, 401)
                return

            params = parse_qs(parsed.query)
            query = params.get("q", [""])[0]
            if not query:
                self.send_json({"error": "Missing ?q= parameter"}, 400)
                return

            count = params.get("count", ["12"])[0]
            offset = params.get("offset", ["0"])[0]
            url = f"{BRAVE_URL}?q={quote(query)}&count={count}&offset={offset}"

            try:
                req = Request(url, headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": API_KEY,
                })
                with urlopen(req, timeout=10) as resp:
                    raw = resp.read()
                    # Handle gzip encoding
                    if resp.headers.get('Content-Encoding') == 'gzip':
                        raw = gzip.decompress(raw)
                    data = json.loads(raw.decode())
                self.send_json(data)
            except HTTPError as e:
                err_body = e.read().decode()[:300] if e.fp else str(e)
                self.send_json({"error": f"Brave API error {e.code}: {err_body}"}, e.code)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
            return

        # CORS preflight
        if self.command == "OPTIONS":
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            return

        self.send_error(404, "Not found")

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, fmt, *args):
        print(f"[neonex] {args[0]}", flush=True)

if __name__ == "__main__":
    print(f"╔══════════════════════════════════╗")
    print(f"║   NEONEX Search Proxy           ║")
    print(f"║   http://localhost:{PORT}         ║")
    print(f"╚══════════════════════════════════╝")
    if not API_KEY:
        print(f"⚠  No API key set. Set it via:")
        print(f"   curl 'http://localhost:{PORT}/key?set=YOUR_BRAVE_API_KEY'")
        print(f"   or set the BRAVE_API_KEY env var.")
    else:
        print(f"✓  API key configured ({API_KEY[:8]}...)")
    print()
    server = HTTPServer(("0.0.0.0", PORT), Proxy)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
