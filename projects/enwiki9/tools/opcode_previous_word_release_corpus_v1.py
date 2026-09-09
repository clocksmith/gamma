#!/usr/bin/env python3
"""Bounded standalone release replay with optional external word witnesses."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import types

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
from opcode_previous_word_compact_observe_v1 import execute as compact_execute

_path = ROOT / 'tools/opcode_previous_word_corpus_v1.py'
_source = _path.read_bytes()
if hashlib.sha256(_source).hexdigest() != '5edbb4d21d4c94ac6fc63fb26bf40ab2b448ed0312ad35b2cc38ead70e108755':
    raise ValueError('immutable bounded corpus helper differs')
_base = types.ModuleType(__name__ + '_bounded_parent')
_base.__file__ = str(_path)
exec(compile(_source, str(_path), 'exec'), vars(_base))
load = _base.load
RAW_LIMIT, ARCHIVE_LIMIT = _base.RAW_LIMIT, _base.ARCHIVE_LIMIT


def release_execute(module, operation, data, arm, observed=True):
    if arm != 'D':
        raise ValueError('release has only treatment D')
    if not observed:
        # Exercise the delivered namespace without diagnostic configuration.
        return module.namespace()['compress' if operation == 'encode' else 'decompress'](data), None

    class DiagnosticModule:
        def namespace(self, selected):
            if selected != 'D':
                raise ValueError('diagnostic arm differs')
            namespace = module.namespace()
            if '_arm' in namespace:
                raise ValueError('release still requires arm selection')
            namespace['_arm'] = 'D'  # Read only by the external compact observer.
            return namespace

    return compact_execute(DiagnosticModule(), operation, data, 'D', True)


_bounded_execute = types.FunctionType(_base.execute.__code__,
    dict(vars(_base), observe_execute=release_execute), 'bounded_execute', _base.execute.__defaults__)


def execute(module, operation, data, observed=True):
    return _bounded_execute(module, operation, data, 'D', observed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('encode', 'decode'))
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--audit', type=Path)
    args = parser.parse_args()
    limit = RAW_LIMIT if args.operation == 'encode' else ARCHIVE_LIMIT
    if args.input.stat().st_size > limit:
        raise ValueError('input exceeds frozen bound')
    if args.output.exists() or args.audit is not None and args.audit.exists():
        raise ValueError('output already exists')
    start, cpu = time.monotonic(), time.process_time()
    output, audit = execute(load(args.candidate_root / 'program.py'), args.operation,
                            args.input.read_bytes(), args.audit is not None)
    with args.output.open('xb') as stream:
        stream.write(output)
    if args.audit is not None:
        with args.audit.open('x') as stream:
            json.dump(audit, stream, sort_keys=True, indent=2)
            stream.write('\n')
    print(json.dumps(dict(output_bytes=len(output), cpu_seconds=time.process_time()-cpu,
                         elapsed_seconds=time.monotonic()-start,
                         peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))


if __name__ == '__main__':
    main()
