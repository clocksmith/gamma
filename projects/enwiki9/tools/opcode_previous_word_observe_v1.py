#!/usr/bin/env python3
"""Optional complete-history and unchanged-parse witnesses for word contexts."""
import hashlib
import argparse
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from opcode_field_compact_observe_v1 import observe as parent_observe
from opcode_field_compact_observe_v1 import load
from opcode_field_repair_cli_v1 import Audit, feed


def history(state, required=False):
    """Include the parent's restored parser field as well as added word state."""
    if required and not callable(getattr(state, 'completed_words', None)):
        raise ValueError('missing completed-word state')
    words = state.completed_words() if hasattr(state, 'completed_words') else (b'', b'')
    if len(words) != 2 or any(type(w) is not bytes or len(w) > 8 for w in words):
        raise ValueError('invalid completed-word state')
    return (state.modeled_f, words)


class WordAudit(Audit):
    def __init__(self, arm):
        # Every arm uses the already repaired parent's field projection.
        super().__init__('D')
        if arm not in 'PKDS' or len(arm) != 1:
            raise ValueError('unknown word arm')
        self.require_words = arm != 'P'
        self.word_hash = hashlib.sha256(b'opcode-previous-word-history-v1')
        self.parse_hash = hashlib.sha256(b'opcode-previous-word-parse-v1')
        self.parse_events = 0
        self.mode = None
        self.updates_by_mode = [0, 0, 0]
        self.word_checkpoints = []

    def byte(self, state, byte):
        super().byte(state, byte)
        feed(self.word_hash, (state.position, byte, history(state, self.require_words)))
        if self.bytes % 4096 == 0:
            self.word_checkpoints.append((self.bytes, self.word_hash.hexdigest()))

    def transition(self, event):
        super().transition(event)
        if event[0] == 0:
            if self.mode not in (0, 1, 2):
                raise ValueError('literal update before decoded mode')
            self.updates_by_mode[self.mode] += 1

    def parsed(self, event):
        if event[0] == 0:
            self.mode = event[-1]
        feed(self.parse_hash, event)
        self.parse_events += 1

    def finish(self, ns, coder, literal, state, tokens, chains, reconstructed):
        parent = super().finish(ns, coder, literal, state, tokens, chains, reconstructed)
        terminal = hashlib.sha256(b'opcode-previous-word-complete-state-v1')
        word_state = history(state, self.require_words)
        feed(terminal, (parent['terminal_common_state_sha256'], word_state))
        if sum(self.updates_by_mode) != parent['predictor_bits'] or parent['predictor_bits'] != 8*self.bytes:
            raise ValueError('incomplete reconstructed-byte prediction updates')
        if not self.word_checkpoints or self.word_checkpoints[-1][0] != self.bytes:
            self.word_checkpoints.append((self.bytes, self.word_hash.hexdigest()))
        return dict(parent=parent, word_history_sha256=self.word_hash.hexdigest(),
                    word_checkpoints=self.word_checkpoints,
                    completed_words_hex=[w.hex() for w in word_state[1]],
                    modeled_field=state.modeled_f,
                    complete_state_sha256=terminal.hexdigest(),
                    parse_sha256=self.parse_hash.hexdigest(), parse_events=self.parse_events,
                    updates_by_mode=self.updates_by_mode,
                    witness_scope='Parent common events/tables plus every reconstructed-byte history update and terminal added state; hashes, not full intermediate snapshots.')


def observe(ns, arm):
    audit = WordAudit(arm)
    BaseTOK = ns['TOK']

    class Tokens(BaseTOK):
        def eve(self, coder, state, mode):
            audit.parsed((0, state.position, mode))
            return super().eve(coder, state, mode)

        def evd(self, coder, state):
            mode = super().evd(coder, state)
            audit.parsed((0, state.position, mode))
            return mode

        def rawe(self, coder, length, distance):
            audit.parsed((1, length, distance))
            return super().rawe(coder, length, distance)

        def rawd(self, coder):
            result = super().rawd(coder)
            audit.parsed((1,) + result)
            return result

        def chaine(self, coder, state, level, index, length):
            audit.parsed((2, level, index, length))
            return super().chaine(coder, state, level, index, length)

        def chaind(self, coder, state):
            result = super().chaind(coder, state)
            audit.parsed((2,) + result)
            return result

    ns['TOK'] = Tokens
    return parent_observe(ns, audit)


def execute(module, operation, data, arm, observed=True):
    if operation not in ('encode', 'decode'):
        raise ValueError('unknown operation')
    ns = module.namespace(arm)
    captured = observe(ns, arm) if observed else None
    out = ns['compress' if operation == 'encode' else 'decompress'](data)
    return out, captured['audit'] if observed else None


def compare_audits(expected, actual):
    """Refuse missing or replaced supplemental history and synchronization data."""
    required = {'parent', 'word_history_sha256', 'word_checkpoints',
                'completed_words_hex', 'modeled_field', 'complete_state_sha256',
                'parse_sha256', 'parse_events', 'updates_by_mode', 'witness_scope'}
    if not required.issubset(expected) or not required.issubset(actual):
        raise ValueError('missing word observation')
    if expected != actual:
        raise ValueError('word observation differs')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('encode', 'decode'))
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--arm', choices=tuple('PKDS'), required=True)
    parser.add_argument('--audit', type=Path)
    args = parser.parse_args()
    # Synthetic command surface. A corpus runner needs its own frozen bounds.
    limit = 4096 if args.operation == 'encode' else 32768
    if args.input.stat().st_size > limit:
        raise ValueError('synthetic input bound')
    if args.output.exists() or args.audit is not None and args.audit.exists():
        raise ValueError('output already exists')
    start, cpu = time.monotonic(), time.process_time()
    out, report = execute(load(args.candidate_root / 'program.py'), args.operation,
                          args.input.read_bytes(), args.arm, args.audit is not None)
    if len(out) > (4096 if args.operation == 'decode' else 32768):
        raise ValueError('synthetic output bound')
    with args.output.open('xb') as stream:
        stream.write(out)
    if args.audit is not None:
        with args.audit.open('x') as stream:
            json.dump(report, stream, sort_keys=True, indent=2)
            stream.write('\n')
    print(json.dumps(dict(output_bytes=len(out), cpu_seconds=time.process_time()-cpu,
                          elapsed_seconds=time.monotonic()-start,
                          peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))


if __name__ == '__main__':
    main()
