"""Serve local BITS with a same-origin, read-only problem discovery endpoint."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import signal
from urllib.parse import unquote, urlsplit

from .bits_recognition import BitsRecognizer
from .doppler_runtime import DopplerRuntime, sha


DEFAULT_PROFILE = Path(__file__).with_name('config')/'bits-reranker-tiled-v1'


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Never log query text or private artifact paths.

    def valid_host(self):
        return self.headers.get('Host') in {f'localhost:{self.server.server_port}', f'127.0.0.1:{self.server.server_port}'}

    def send_json(self, status, value):
        body = json.dumps(value, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):pass

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def safe_static(self):
        if not self.valid_host():return False
        root = Path(self.directory).resolve()
        path = (root/unquote(urlsplit(self.path).path).lstrip('/')).resolve()
        return path.is_relative_to(root) and not any(p.startswith('.') for p in path.relative_to(root).parts)

    def do_GET(self):
        if not self.safe_static():
            self.send_json(403, {'error': 'Forbidden'}); return
        super().do_GET()

    def do_HEAD(self):
        if not self.safe_static():
            self.send_error(403); return
        super().do_HEAD()

    def list_directory(self, path):
        self.send_error(404)
        return None

    def do_POST(self):
        origin = 'http://'+self.headers.get('Host', '')
        if (not self.valid_host() or self.headers.get('Origin') != origin
                or self.headers.get('X-Bits-Request') != 'recognize'):
            self.send_json(403, {'error': 'Use the local BITS page.'}); return
        try:
            if self.path != '/api/bits/recognize' or self.headers.get('Content-Type') != 'application/json':
                raise ValueError('Invalid recognition request.')
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536:raise ValueError('Request is too large.')
            request = json.loads(self.rfile.read(length))
            if type(request) is not dict or set(request) != {'text', 'request_id'}:
                raise ValueError('Invalid recognition request.')
            ident = request['request_id']
            if type(ident) is not str or not 1 <= len(ident) <= 100:
                raise ValueError('Invalid request identity.')
            result = self.server.recognizer.recognize(request['text'])
            self.send_json(200, dict(result, request_id=ident))
        except (ValueError, TypeError, KeyError):
            self.send_json(400, {'error': 'Check the problem description.'})
        except RuntimeError:
            self.send_json(503, {'error': 'Recognition is unavailable. Try again.'})
        except Exception:
            self.send_json(503, {'error': 'Recognition is unavailable. Try again.'})


def create_server(public_root, recognizer, port=8874):
    server = ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, directory=str(Path(public_root).resolve())))
    server.recognizer = recognizer
    server.daemon_threads = True
    return server


def argument_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('public-root', 'keys', 'vectors', 'gate', 'doppler-root', 'embedding-model', 'reranker-model'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--gate-sha256', required=True)
    parser.add_argument('--port', type=int, default=8874)
    parser.add_argument('--surface', choices=('node', 'browser'), default='node')
    parser.add_argument('--reranker-config', type=Path,
                        help='Explicit Doppler runtime configuration; bound into index identity')
    return parser


def create_recognizer(args):
    config_path = args.reranker_config or DEFAULT_PROFILE/'runtime-config.json'
    if config_path.stat().st_size > 1024**2:
        raise ValueError('runtime configuration exceeds one MB')
    if args.reranker_config is None:
        preparation = json.loads((DEFAULT_PROFILE/'preparation.json').read_text())
        if (sha(args.reranker_model/'manifest.json') != preparation['manifest_sha256']
                or sha(config_path) != preparation['runtime_config_sha256']):
            raise ValueError('Default BITS profile does not bind these artifacts; provide an explicit --reranker-config.')
    reranker_config = json.loads(config_path.read_text())
    if type(reranker_config) is not dict:
        raise ValueError('runtime configuration must be an object')
    def runtime_factory():
        return DopplerRuntime(args.doppler_root, args.embedding_model, args.reranker_model,
                              timeout=90, surface=args.surface,
                              reranker_config=reranker_config)
    runtime = runtime_factory()
    try:
        return BitsRecognizer(public_root=args.public_root, keys=args.keys, vectors=args.vectors,
                              gate=args.gate, gate_sha256=args.gate_sha256, runtime=runtime,
                              runtime_factory=runtime_factory)
    except BaseException:
        runtime.close()
        raise


def main():
    args = argument_parser().parse_args()
    recognizer = create_recognizer(args)
    server = create_server(args.public_root, recognizer, args.port)
    def stop(*_):raise SystemExit(0)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    print(f'BITS: http://127.0.0.1:{server.server_port}/labs/two-button/', flush=True)
    try:server.serve_forever()
    finally:
        server.server_close()
        recognizer.close()


if __name__ == '__main__':
    main()
