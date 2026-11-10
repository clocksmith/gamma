"""Two-phase, source-bound synthetic direct BITS composition evidence.

Select writes immutable first-match decisions and all rejection traces before
score generates evaluation cases. Neither command accesses corpus populations,
native solution source, protected reservations, or the existing native judge.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT))
from algsolve.synth import direct_bits_oracles as oracles
from algsolve.synth import direct_bits_search as search
from algsolve.synth import typed_vector_program as runtime
from algsolve.synth import typed_word_codec as codec

SCHEMA = 'algsolve.direct-bits-development-evidence.v1'


def sha(data): return hashlib.sha256(data).hexdigest()
def encoded(value): return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def sources():
    paths = [Path(__file__), Path(oracles.__file__), Path(search.__file__),
             Path(runtime.__file__), Path(codec.__file__),
             PROJECT / 'algsolve/__init__.py', PROJECT / 'algsolve/synth/__init__.py']
    return {str(p.relative_to(PROJECT)): {'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size}
            for p in paths}


def write_once(path, data):
    """Preserve earlier decisions/results rather than silently replacing them."""
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Existing evidence differs; use a new output directory: ' + str(path))
    else:
        with path.open('xb') as stream:
            stream.write(data)


def select(directory):
    directory.mkdir(parents=True, exist_ok=True)
    # Evaluation inputs/answers are not generated during selection.
    tasks = oracles.tasks(include_evaluation=False)
    requests = [[(c.inputs, c.expected) for c in t.train_cases] for t in tasks]
    result = search.synthesize(requests)
    trace = b''.join((search.canonical(row) + '\n').encode() for row in result.trace)
    write_once(directory / 'trace.jsonl', trace)
    decision = {'schema': SCHEMA, 'phase': 'frozen-selection', 'source_bindings': sources(),
                'grammar': search.grammar(), 'grammar_sha256': search.digest(search.grammar()),
                'training_sha256': search.digest(requests),
                'trace_sha256': sha(trace), 'trace_bytes': len(trace),
                'candidates_tested': result.candidates_tested,
                'training_executions': result.training_executions,
                'training_operation_units': result.training_operation_units,
                'training_attempted_operation_units': result.training_attempted_operation_units,
                'failed_training_executions': result.failed_training_executions,
                'rows': [{'task': task.name, 'training_examples': len(task.train_cases),
                          'selection': selection, 'status': 'selected' if selection else 'search_exhausted'}
                         for task, selection in zip(tasks, result.selections)],
                'evidence_scope': 'Synthetic example-conditioned development search only. No task identity, oracle callable, test input or test answer reaches the composer. No protected/generalization/native qualification.'}
    write_once(directory / 'selection.json', encoded(decision))
    return decision, {'search_wall_seconds': result.elapsed_seconds}


def score(directory):
    selection_bytes = (directory / 'selection.json').read_bytes()
    decision = json.loads(selection_bytes)
    if decision['source_bindings'] != sources():
        raise ValueError('Source bindings changed since selection')
    trace = (directory / 'trace.jsonl').read_bytes()
    if sha(trace) != decision['trace_sha256'] or len(trace) != decision['trace_bytes']:
        raise ValueError('Search trace changed since selection')
    attempts = [json.loads(line) for line in trace.splitlines()]
    if (len(attempts) != decision['candidates_tested'] or
            [a['ordinal'] for a in attempts] != list(range(len(attempts)))):
        raise ValueError('Search trace order/count mismatch')
    if (decision['schema'] != SCHEMA or decision['phase'] != 'frozen-selection' or
            decision['grammar_sha256'] != search.digest(search.grammar()) or
            search.canonical(decision['grammar']) != search.canonical(search.grammar())):
        raise ValueError('Selection protocol mismatch')
    tasks = oracles.tasks()
    if [r['task'] for r in decision['rows']] != [t.name for t in tasks]:
        raise ValueError('Task inventory changed since selection')
    training = [[(c.inputs, c.expected) for c in t.train_cases] for t in tasks]
    if search.digest(training) != decision['training_sha256']:
        raise ValueError('Training contract changed since selection')
    rows = []
    started = time.perf_counter()
    for task_index, (task, row) in enumerate(zip(tasks, decision['rows'])):
        expected_status = 'selected' if row['selection'] is not None else 'search_exhausted'
        first_matches = [a for a in attempts if task_index in a['new_matches']]
        if row['status'] != expected_status or (row['selection'] is None and first_matches):
            raise ValueError('Selection status or trace match mismatch')
        result = {'task': task.name, 'contract_sha256': task.contract_hash(),
                  'description': task.description, 'domain': vars(task.domain),
                  'training_cases': len(task.train_cases), 'evaluation_cases': len(task.evaluation_cases),
                  'status': row['status'], 'widths': []}
        for case in task.train_cases + task.evaluation_cases:
            task.domain.validate(case.inputs[0])
        train_keys = {search.canonical(c.inputs) for c in task.train_cases}
        if any(search.canonical(c.inputs) in train_keys for c in task.evaluation_cases):
            raise ValueError('Training and evaluation inputs overlap')
        if row['selection'] is not None:
            selected = row['selection']
            packet = bytes.fromhex(selected['packet_hex'])
            if sha(packet) != selected['packet_sha256']:
                raise ValueError('Selected packet hash mismatch')
            graph = codec.decode(packet)
            if search.digest(graph) != selected['graph_sha256']:
                raise ValueError('Selected graph hash mismatch')
            if (len(first_matches) != 1 or first_matches[0]['ordinal'] != selected['ordinal'] or
                    first_matches[0]['failure'] is not None or
                    search.canonical(first_matches[0]['plan']) != search.canonical(selected['plan'])):
                raise ValueError('Selected graph does not match its search trace')
            # A receipt cannot smuggle a different graph under a plausible plan.
            plan = selected['plan']
            planned_graph = search.compile_plan(plan['stages'], plan['terminal'])
            if search.digest(planned_graph) != first_matches[0]['graph_sha256']:
                raise ValueError('Plan and trace graph hash differ')
            reconstructed, _ = codec.encode(planned_graph, 6, 'vector-v1')
            if reconstructed != packet:
                raise ValueError('Selection plan and packet differ')
            if codec.costs(packet) != selected['packet_cost']:
                raise ValueError('Selected packet cost mismatch')
            training_verdict = search.evaluate_packet(packet, [(c.inputs, c.expected) for c in task.train_cases],
                                                      budget=task.budget)
            if not training_verdict['passed']:
                raise ValueError('Frozen selection fails its training contract')
            for width in (6, 7, 8):
                recoded, costs = codec.encode(graph, width, 'vector-v1')
                if codec.decode(recoded) != graph:
                    raise ValueError('Width re-encoding changed the graph')
                verdict = search.evaluate_packet(recoded, [(c.inputs, c.expected) for c in task.evaluation_cases],
                                                 budget=task.budget)
                result['widths'].append({'width': width, 'costs': costs, 'evaluation': verdict})
            result['status'] = ('independent_development_passed' if all(w['evaluation']['passed'] for w in result['widths'])
                                else 'independent_development_failed')
        rows.append(result)
    descriptor = codec.descriptor('vector-v1')
    initializers = sum(item['bytes'] for path, item in sources().items() if path.endswith('__init__.py'))
    execution_support = (descriptor['dictionary_bytes'] + descriptor['decoder_source_bytes'] +
                         descriptor['runtime_source_bytes'] + initializers)
    packages = []
    for width in (6, 7, 8):
        packet_bits = sum(w['costs']['packet_bits'] for row in rows for w in row['widths'] if w['width'] == width)
        packages.append({'width': width, 'selected_programs': sum(bool(r['widths']) for r in rows),
                         'packet_bytes': packet_bits // 8, 'shared_execution_support_bytes': execution_support,
                         'executable_package_bytes': packet_bits // 8 + execution_support})
    report = {'schema': SCHEMA, 'phase': 'independent-development-scored',
              'selection_sha256': sha(selection_bytes), 'source_bindings': sources(),
              'task_count': len(tasks), 'independent_development_passed': sum(r['status'] == 'independent_development_passed' for r in rows),
              'abstained': sum(r['status'] == 'search_exhausted' for r in rows),
              'independent_development_failed': sum(r['status'] == 'independent_development_failed' for r in rows),
              'test_executions': sum(w['evaluation']['cases'] for r in rows for w in r['widths']),
              'rows': rows, 'packages': packages, 'runtime_descriptor': descriptor,
              'composer_source_bytes': Path(search.__file__).stat().st_size,
              'oracle_source_bytes': Path(oracles.__file__).stat().st_size,
              'measurement_source_bytes': Path(__file__).stat().st_size,
              'accounting': 'Each width is an alternative package: all selected packets plus shared dictionary, decoder, owned-vector runtime and package initializers once. Composer, oracle, measurement and trace bytes are additional research tooling, disclosed separately. Python and standard library binaries are external unmeasured dependencies. Operation units are explicit interpreter charges, not native instructions or proof of asymptotic complexity.',
              'evidence_scope': '26 authored synthetic development specifications, first-match example-conditioned finite enumeration, disjoint independent oracle inputs. No catalogue problem count, natural-language synthesis, unseen-family qualification, native JavaScript/Python acceptance, human fluency, or M1-M6 completion.'}
    write_once(directory / 'evaluation.json', encoded(report))
    return report, {'evaluation_wall_seconds': time.perf_counter() - started}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('select', 'score', 'all'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    timing = {}
    if args.phase in ('select', 'all'):
        _, measured = select(args.output)
        timing.update(measured)
    if args.phase in ('score', 'all'):
        report, measured = score(args.output)
        timing.update(measured)
        print(json.dumps({key: report[key] for key in ('task_count', 'independent_development_passed', 'abstained',
                                                      'independent_development_failed', 'test_executions')}))
    print(json.dumps(timing, sort_keys=True))


if __name__ == '__main__':
    main()
