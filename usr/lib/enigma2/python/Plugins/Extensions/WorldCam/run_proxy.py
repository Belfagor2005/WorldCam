#!/usr/bin/python
#  Completely rewritten and optimized Lululla
#  Version: 1.0

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests


class HLSProxyHandler(BaseHTTPRequestHandler):
    def __init__(self, player_instance, *args, **kwargs):
        self.player = player_instance
        super().__init__(*args, **kwargs)

    @property
    def logger(self):
        return self.player.logger if self.player else None

    def do_GET(self):
        try:
            # Gestisce le richieste per la playlist M3U8
            if self.path.startswith("/proxy.m3u8"):
                query = urlparse(self.path).query
                params = parse_qs(query)
                target_url = params.get('url', [''])[0]

                if not target_url:
                    self.send_error(404, 'Missing URL parameter')
                    return

                # Genera un playlist M3U8 fittizia
                m3u8_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:10.0,
{target_url}
#EXT-X-ENDLIST"""

                self.send_response(200)
                self.send_header(
                    'Content-Type',
                    'application/vnd.apple.mpegurl')
                self.end_headers()
                self.wfile.write(m3u8_content.encode('utf-8'))
                return

            # Gestisce le richieste per lo stream video
            elif self.path.startswith("/video"):
                query = urlparse(self.path).query
                params = parse_qs(query)
                target_url = params.get('url', [''])[0]

                if not target_url:
                    self.send_error(404, 'Missing URL parameter')
                    return

                # Estrae il video ID per generare i cookie
                from re import search
                video_id_match = search(r'[&?]v=([^&]+)', target_url)
                video_id = video_id_match.group(
                    1) if video_id_match else 'unknown'

                # Header necessari per bypassare la protezione di YouTube
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
                    'Referer': f'https://www.youtube.com/watch?v={video_id}',
                    'Origin': 'https://www.youtube.com',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-site',
                    'Pragma': 'no-cache',
                    'Cache-Control': 'no-cache'}

                # Effettua la richiesta allo stream reale
                response = requests.get(
                    target_url,
                    headers=headers,
                    stream=True,
                    timeout=10,
                    allow_redirects=True
                )

                # Restituisci la risposta al player
                self.send_response(response.status_code)
                for key, value in response.headers.items():
                    if key.lower() not in [
                            'transfer-encoding', 'connection', 'keep-alive']:
                        self.send_header(key, value)
                self.end_headers()

                # Stream del contenuto
                for chunk in response.iter_content(chunk_size=8192):
                    self.wfile.write(chunk)

                return

        except Exception as e:
            self.logger.error(f"Proxy error: {str(e)}")
            self.send_error(500, str(e))

        self.send_error(404, 'Not Found')


def run_proxy_server(player_instance):
    """Avvia il server proxy con riferimento all'istanza del player"""
    server = HTTPServer(('127.0.0.1', 8000),
                        lambda *args: HLSProxyHandler(player_instance, *args))
    print("HLS proxy server started on port 8000")
    server.serve_forever()


if __name__ == '__main__':
    run_proxy_server()
