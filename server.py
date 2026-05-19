#!/usr/bin/env python3
"""HTTP server for Promise Gap Analyser UI."""

import json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

class APIHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/films':
            self.send_json(self.get_films())
            return

        if path.startswith('/api/film/'):
            slug = path.split('/')[-1]
            film_data = self.get_film(slug)
            if film_data:
                self.send_json(film_data)
            else:
                self.send_error(404)
            return

        if path == '/':
            self.path = '/index.html'

        return SimpleHTTPRequestHandler.do_GET(self)

    def get_films(self):
        films = []
        for p in Path('data/processed').glob('*_result.json'):
            with open(p) as f:
                data = json.load(f)
            films.append({
                'slug': data['film'],
                'title': data.get('filmTitle', data.get('title', '')),
                'gapScore': data.get('gapScore', data.get('gap_score', 0)),
                'failureMode': data.get('failureMode', data.get('verdict', '')),
                'posterUrl': data.get('posterUrl', ''),
            })
        return sorted(films, key=lambda x: x['gapScore'])

    def get_film(self, slug):
        path = Path(f'data/processed/{slug}_result.json')
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

if __name__ == '__main__':
    server = HTTPServer(('localhost', 5001), APIHandler)
    print("Promise Gap Analyser server running at http://localhost:5001")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
