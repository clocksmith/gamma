"""Independent synthetic falsifiers for the fixed-graph event interpreter."""
import hashlib
import json
import os
from pathlib import Path
import unittest

from tools import dualstream_event_codec_v1 as codec
from tools import dualstream_grammar_v1 as old
from tools import dualstream_grammar_reserialize_v1 as rep

ROOT = Path(__file__).resolve().parents[1]
RETAIN = Path(os.environ['GAMMA_EVENT_REVIEW_RETAIN']) if os.environ.get('GAMMA_EVENT_REVIEW_RETAIN') else None


def save(path, value):
    if RETAIN is None:
        return
    destination = RETAIN / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    with destination.open('xb') as stream:
        stream.write(data)


class ObservedChannel(codec.EventChannel):
    def __init__(self, mode, payload=None):
        super().__init__(mode, payload)
        self.schedule, self.emissions, self.argument_prefixes = [], [], []

    def event(self, kind, alphabet, value=None, context=(), category='program'):
        if kind == codec.ARG_BYTE:
            self.argument_prefixes.append((value, self.state_digest()))
        decoded = super().event(kind, alphabet, value, context, category)
        self.schedule.append((kind, alphabet, decoded, context, category))
        return decoded

    def emit(self, data):
        self.emissions.append(bytes(data))
        return super().emit(data)


class IndependentEventInterpreterTests(unittest.TestCase):
    def test_content_phrase_survives_literal_and_nonmonotonic_template_roots(self):
        body = (old.Arg(2), old.Arg(0), b'/', old.Arg(2), old.Arg(1), old.Arg(0))
        model = old.Model(
            structure=(('content', 1), ('literal', b'<gap>'), ('call', 0), ('content', 2),
                       ('literal', b'!'), ('call', 0), ('content', 1)),
            content=(old.Ref(2),), arguments=(b'', b'bb', b'ccc', b'_', b'd', b'ee'),
            phrases=((b'A', b'B'), (b'C', b'D'), (old.Ref(0), old.Ref(1))),
            templates=((3, body),))
        raw = b'A<gap>ccc/cccbbBC!ee_/eed_D'
        self.assertLessEqual(len(raw), 8192)
        frame, _ = old.frame_bytes(raw, 'parameter', model)
        selected = old.HEADER.pack(old.MAGIC, old.MAX_FRAME, 1, len(raw)) + frame
        self.assertEqual(old.decode(selected), raw)
        schedules = {}
        for mode in ('G', 'X'):
            channel = ObservedChannel(mode)
            interpreter = codec.Interpreter(channel, len(raw), model)
            output, restored_model, execution = interpreter.run()
            payload, sync = channel.finish()
            self.assertEqual(output, raw)
            self.assertEqual(rep.graph(restored_model), rep.graph(model))
            self.assertEqual(restored_model.content, (old.Ref(2),))
            self.assertEqual(restored_model.arguments, model.arguments)
            self.assertEqual(execution['repeated_argument_references'], 4)
            self.assertEqual(execution['boundary_count'], len(model.structure) + 1)
            self.assertEqual([row[2] for row in channel.schedule if row[0] == codec.ARG_LENGTH], [3, 0, 2, 2, 1, 1])
            decoded_channel = ObservedChannel(mode, payload)
            decoded = codec.Interpreter(decoded_channel, len(raw))
            inverse, inverse_model, inverse_execution = decoded.run()
            _, inverse_sync = decoded_channel.finish()
            self.assertEqual((inverse, rep.graph(inverse_model), inverse_execution), (raw, rep.graph(model), execution))
            self.assertEqual(sync, inverse_sync)
            self.assertEqual(channel.schedule, decoded_channel.schedule)
            self.assertEqual(channel.emissions, decoded_channel.emissions)
            archive, report = codec.encode(selected, mode)
            self.assertEqual(codec.decode(archive), (raw, report))
            self.assertEqual(codec.encode(selected, mode), (archive, report))
            self.assertEqual(sum(report['costs'].values()), len(archive))
            schedules[mode] = channel.schedule
            for name, data in [('archive.bin', archive), ('raw.bin', raw), ('payload.bin', payload),
                               ('report.json', report), ('execution.json', execution), ('schedule.json', channel.schedule)]:
                save(mode + '/' + name, data)
        # Event kinds, values, alphabets, order, interpreter contexts and byte
        # emissions are fixed. Prediction alone may condition on context in X.
        self.assertEqual(schedules['G'], schedules['X'])

    def test_future_argument_value_is_absent_from_pretruth_channel_state(self):
        histories = []
        for future in (b'cedar', b'maple'):
            model = old.Model(structure=(('call', 0), ('call', 0)), arguments=(b'oak', future),
                              templates=((1, (b'[', old.Arg(0), b']')),))
            raw = b'[oak][' + future + b']'
            channel = ObservedChannel('X')
            codec.Interpreter(channel, len(raw), model).run()
            channel.finish()
            histories.append(channel.argument_prefixes)
        self.assertEqual(len(histories[0]), 8)
        self.assertEqual(histories[0][:3], histories[1][:3])
        self.assertNotEqual(histories[0][3][0], histories[1][3][0])
        self.assertEqual(histories[0][3][1], histories[1][3][1])
        save('future-prefix.json', {'pretruth_boundaries_equal': 4, 'argument_bytes': 8,
                                  'first_future_values': [histories[0][3][0], histories[1][3][0]]})

    def test_boundary_binds_retained_definitions_and_unemitted_pending_cursor(self):
        def machine(first=b'A'):
            model = old.Model(content=(old.Ref(1),), phrases=((first, b'B'), (old.Ref(0), b'C')))
            item = codec.Interpreter(codec.EventChannel('G'), 3, model)
            item.definitions()
            return item
        first, second = machine(b'A'), machine(b'D')
        self.assertEqual(first.execution.digest(), second.execution.digest())
        self.assertEqual(first.output, second.output)
        first.boundary(0)
        second.boundary(0)
        self.assertNotEqual(first.boundaries.digest(), second.boundaries.digest())
        first, second = machine(), machine()
        first.execute(('content', 1))
        second.execute(('content', 1))
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.execution.digest(), second.execution.digest())
        second.pending.pop()
        first.boundary(1)
        second.boundary(1)
        self.assertNotEqual(first.boundaries.digest(), second.boundaries.digest())
        save('boundary-falsifier.json', {'definitions_detected_without_output': True,
                                        'pending_cursor_change_detected_without_output': True})

    def test_exponential_empty_phrase_cache_rejects_at_declared_bound(self):
        phrases = [(b'', b'')]
        for index in range(1, 25):
            phrases.append((old.Ref(index - 1), old.Ref(index - 1)))
        model = old.Model(phrases=tuple(phrases))
        item = codec.Interpreter(codec.EventChannel('G'), 1, model)
        with self.assertRaisesRegex(ValueError, 'phrase expansion bound'):
            item.definitions()
        self.assertEqual(len(item.phrase_leaves[-1]), 2 * old.MAX_FRAME)
        self.assertEqual(len(item.phrases), 17)
        self.assertLess(item.nodes, 64)
        save('malformed-expansion.json', {'retained_phrases': len(item.phrases),
            'largest_retained_leaf_count': len(item.phrase_leaves[-1]), 'stored_nodes': item.nodes,
            'next_temporary_expansion_leaf_upper_bound': 4 * old.MAX_FRAME,
            'rejected': True, 'scope': 'Synthetic malformed graph; no corpus and no rule discovery.'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
