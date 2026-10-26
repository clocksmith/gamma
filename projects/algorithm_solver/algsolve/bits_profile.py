"""Bounded cold/warm diagnostics of the actual BITS discovery route, not qualification."""
import json
from pathlib import Path
import time

from .bits_server import argument_parser, create_recognizer
from .doppler_runtime import sha


def main():
    parser = argument_parser()
    parser.add_argument('--query-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, choices=range(1, 6), default=2)
    args = parser.parse_args()
    if args.query_file.stat().st_size > 32768:
        raise ValueError('query exceeds 32 KB')
    query = args.query_file.read_text()
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    recognizer = create_recognizer(args)
    contract = {'schema': 'gamma.bits-profile.v1', 'recognition_qualified': False,
                'index': recognizer.identity, 'index_sha256': recognizer.identity_sha256,
                'repeats': args.repeats, 'initialization_ms': (time.perf_counter()-started)*1000,
                'code_sha256': {name: sha(Path(__file__).with_name(name)) for name in
                                ('bits_profile.py', 'bits_server.py', 'bits_recognition.py', 'doppler_runtime.py')},
                'scope': 'Repeated development query; no latency distribution or accuracy qualification. '
                         'This discovery route executes no judge and returns no implementations.'}
    (args.output/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    try:
        for i in range(args.repeats):
            start = time.perf_counter()
            try:
                result = recognizer.recognize(query, diagnostics=True)
            except Exception as error:
                result = {'error_type': type(error).__name__, 'error': str(error),
                          'elapsed_ms': (time.perf_counter()-start)*1000}
            result['iteration'] = i
            result['worker_pid'] = getattr(recognizer.runtime.process, 'pid', None)
            (args.output/f'{i}.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
            print(json.dumps({k: result[k] for k in ('iteration', 'worker_pid', 'timings', 'error_type') if k in result}), flush=True)
            if 'error_type' in result:
                raise RuntimeError('Profile failed; retained original failure in output')
    finally:
        recognizer.close()


if __name__ == '__main__':
    main()
