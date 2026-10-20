"""Trusted host-only868 raw replay. Never imports author codecs or harnesses."""
import base64
import dataclasses
import hashlib
import json
import math
import re
from pathlib import Path
from algsolve import validate
from algsolve.judge import judge, sandbox
from .campaign_868_integer import need, sha, ref, check, digest, PROFILE, ANCHORS
from . import campaign_toolchain

TAG = '__gamma_uint_decimal_v1__'
SAFE = 2**53 - 1
MAXIMUM = 10**1024 - 1

def bs(value):
    return hashlib.sha256(value.encode() if type(value) is str else value).hexdigest()

def compact(value):
    return json.dumps(value, ensure_ascii=True, separators=(',', ':'), allow_nan=False)

def unique(pairs):
    result = {}
    for name, value in pairs:
        need(name not in result, 'Duplicate JSON field')
        result[name] = value
    return result

def reject_constant(value):
    raise ValueError('Nonfinite JSON constant')

def canonical(raw):
    if type(raw) is bytes:
        raw = raw.decode('ascii')
    value = json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    need(compact(value) == raw, 'Noncanonical raw transport')
    return value

def integer(value):
    need(type(value) is dict and set(value) == {TAG} and
         type(value[TAG]) is str and re.fullmatch(r'(?:0|[1-9][0-9]{0,1023})',
                                                 value[TAG], re.ASCII) is not None,
         'Invalid uint1024 decimal envelope')
    return int(value[TAG])

def encode_calls(cases):
    need(type(cases) is list and bool(cases), 'Nonempty original cases required')
    calls = []
    for case in cases:
        need(type(case) is dict and type(case.get('args')) is list and
             len(case['args']) == 1 and not case.get('kwargs') and
             type(case['args'][0]) is int and 0 <= case['args'][0] <= MAXIMUM,
             'One exact uint1024 positional input required')
        calls.append({'args': [{TAG: str(case['args'][0])}]})
    return compact({'profile': PROFILE, 'entry': 'Solution.binaryGap', 'calls': calls}).encode('ascii')

def records(raw, count):
    need(type(count) is int and count > 0, 'Exact positive count required')
    rows = [canonical(line) for line in raw.splitlines()]
    need(len(rows) == count + 1 and type(rows[-1]) is dict and
         set(rows[-1]) == {'done'} and type(rows[-1]['done']) is int and
         rows[-1]['done'] == count, 'Incomplete raw records')
    for index, row in enumerate(rows[:-1]):
        need(type(row) is dict and type(row.get('i')) is int and row['i'] == index and
             'done' not in row, 'Wrong exact ordered index')
    return rows

def decode(raw, cases, language):
    need(language in ['python', 'javascript'], 'Explicit language required')
    encode_calls(cases)
    rows = records(raw, len(cases))
    fields = {'i', 'result', 'args_before', 'args_after', 'argument_runtime_types',
              'result_runtime_type', 'input_object_count', 'returned_input_ids',
              'input_node_values_preserved'}
    decoded = []
    for row, case in zip(rows[:-1], cases):
        need(set(row) == fields, 'Wrong observation shape')
        kind = 'int' if language == 'python' else 'number' if case['args'][0] <= SAFE else 'bigint'
        need(row['argument_runtime_types'] == [kind] and
             row['result_runtime_type'] == ('int' if language == 'python' else 'number'),
             'Argument/output runtime type differs')
        need(type(row['input_object_count']) is int and row['input_object_count'] == 0 and
             row['returned_input_ids'] == [] and row['input_node_values_preserved'] is True,
             'Primitive alias contract failed')
        out = dict(row, result=integer(row['result']))
        need(out['result'] <= 3401, 'Result exceeds binary gap bound')
        for name in ['args_before', 'args_after']:
            need(type(row[name]) is list and len(row[name]) == 1, 'Wrong argument slots')
            out[name] = [integer(row[name][0])]
            need(out[name] == case['args'], 'Exact input roundtrip/mutation failed')
        decoded.append(out)
    return decoded + [rows[-1]]

def native_result(value):
    need(type(value) is dict and set(value) == {
        'exit_code', 'signal', 'stdout', 'stderr', 'wall_seconds', 'timed_out',
        'output_limit_exceeded', 'notes', 'ok'}, 'Incomplete native status')
    value = dict(value)
    declared = value.pop('ok')
    for name in ['stdout', 'stderr']:
        blob = value[name]
        need(type(blob) is dict and set(blob) == {'encoding', 'data', 'sha256', 'byte_count'},
             'Incomplete raw byte envelope')
        data = base64.b64decode(blob['data'], validate=True)
        need(blob == {'encoding': 'base64', 'data': base64.b64encode(data).decode('ascii'),
                      'sha256': bs(data), 'byte_count': len(data)} and
             type(blob['byte_count']) is int and len(data) <= 4*1024**2,
             'Raw bytes/hash/length differs')
        value[name] = data
    need(type(value['exit_code']) is int and value['exit_code'] == 0 and
         value['signal'] is None and value['timed_out'] is False and
         value['output_limit_exceeded'] is False and type(value['notes']) is list and
         type(value['wall_seconds']) in [int, float] and
         math.isfinite(value['wall_seconds']) and 0 <= value['wall_seconds'] <= 8 and
         declared is True, 'Failed or invalid native status')
    result = sandbox.SandboxResult(**value)
    need(result.ok, 'Native execution failed')
    return result

def replay(bound, refs):
    folder = bound['_folder']
    output = folder / 'results-attempt-001'
    index = {str(Path(r['path']).resolve()): r for r in bound['evidence_index']['artifacts']}
    need(len(index) == len(bound['evidence_index']['artifacts']), 'Duplicate evidence paths')
    def load(path):
        reference = index.get(str(path.resolve()))
        need(reference is not None, 'Unindexed saved evidence')
        refs.append(reference)
        return check(reference)
    freeze = bound['freeze']
    manifest = bound['toolchain_manifest']
    summary = load(output / 'summary.json')
    controls = load(folder / 'controls.json')
    controls_summary = load(output / 'controls-summary.json')
    seen = set()
    def proof(value):
        need(value['contract_sha256'] == ANCHORS['freeze'] and
             value['toolchain_manifest_sha256'] == ANCHORS['toolchain_manifest'] and
             type(value['frozen_files_checked']) is int and value['frozen_files_checked'] == 57 and
             type(value['host_dependencies_checked']) is int and value['host_dependencies_checked'] == 11,
             'Per-call frozen boundary differs')
        need(value['runtime'] == {
            'schema': 'algsolve.toolchain-verification.v1', 'passed': True,
            'executable_count': 4, 'measured_identity_count': 59,
            'host_interpreter_matches_sandbox_python': True,
            'complete_dynamic_closure_claimed': False}, 'Per-call measured runtime differs')
        reader = value['reader']
        need(reader['passed'] is True and reader['selected_claims'] == 2 and
             reader['activation_sha256'] == ANCHORS['reader_activation'] and
             reader['shared_reader_sha256'] == ANCHORS['historical_reader'] and
             all(type(reader[k]) is int and reader[k] == 0 for k in
                 ['candidate_runs', 'corpus_records_decoded', 'imported_test_files_loaded']),
             'Scoped reader boundary differs')
    def raw(call, language=None, source=None, payload=None, cases=None,
            kind='normalized', name=None):
        need(type(call) is int and call not in seen, 'Duplicate/malformed sandbox call')
        seen.add(call)
        row = load(output / f'boundary-{call:05d}.json')
        need(type(row['call']) is int and row['call'] == call and
             row['sandbox_returned'] is True and row['expectations_supplied'] is False and
             row['in_memory_bindings_verified'] is True, 'Missing raw call/binding proof')
        for phase in ['before', 'after']:
            proof(row[phase])
            need(row[phase]['reader']['stage'] == phase + '-' + row['phase'],
                 'Wrong boundary proof phase')
        result = native_result(row['sandbox_result'])
        if language is None:
            need(row['phase'] == 'sandbox-probe' and
                 row['argv'] == ['/usr/bin/python3', '-c', 'print(42)'] and
                 row['input_file_sha256'] == {} and row['approved_input_file_sha256'] is None and
                 row['binding_authority'] is None and result.stdout == b'42\n' and
                 row['protocol'] == {'valid': True, 'kind': 'fixed-probe-or-input-rejection-raw'},
                 'Probe boundary differs')
            return result, [], row
        need(row['argv'] == campaign_toolchain.COMMANDS[language] and
             row['phase'] == 'integer868-' + language, 'Child command differs')
        extension = 'js' if language == 'javascript' else 'py'
        if payload is None:
            payload = encode_calls(cases)
        source_hash = freeze['sources'][f'normalized/0868.{extension}'] if source is None else bs(source)
        files = {'calls.json': bs(payload)}
        if language == 'javascript':
            files.update({'harness.cjs': freeze['sources']['harness.cjs'], 'candidate.cjs': source_hash})
        else:
            files.update({'harness.py': freeze['sources']['harness.py'],
                          'codec.py': freeze['sources']['codec.py'], 'candidate.py': source_hash})
        need(row['input_file_sha256'] == row['approved_input_file_sha256'] == files,
             'Actual candidate/payload/harness/codec hashes differ')
        authority = ({'kind': kind, 'source_relative_path': f'normalized/0868.{extension}'}
                     if kind == 'normalized' else
                     {'kind': kind, 'control_name': name, 'controls_sha256': freeze['sources']['controls.json']})
        need(row['binding_authority'] == authority, 'Wrong source binding authority')
        parsed = [] if cases is None else records(result.stdout, len(cases))
        framing = ({'valid': True, 'kind': 'fixed-probe-or-input-rejection-raw'} if cases is None else
                   {'expected_calls': len(cases), 'valid': True, 'reason': None})
        need(row['protocol'] == framing, 'Saved framing differs')
        return result, parsed, row
    def score(result, decoded, cases):
        translated = dataclasses.replace(result, stdout=('\n'.join(compact(v) for v in decoded)+'\n').encode())
        return judge._score_functional(translated, validate.functional_tests(cases)).to_dict()
    raw(1)
    call = 2
    control_rows = []
    for language in ['python', 'javascript']:
        for offset in range(0, len(controls['positive_cases']), 4):
            cases = controls['positive_cases'][offset:offset+4]
            result, _, _ = raw(call, language, cases=cases)
            verdict = score(result, decode(result.stdout, cases, language), cases)
            need(verdict['passed'], 'Positive profile control failed')
            control_rows.append({'kind': 'positive', 'language': language, 'offset': offset,
                                 'cases': len(cases), 'call_id': call, 'passed': True, 'verdict': verdict})
            call += 1
        for item in controls['invalid_requests']:
            result, _, _ = raw(call, language, controls['sentinel_sources'][language],
                               item['payload_ascii'], kind='input-sentinel', name=item['name'])
            rows = result.stdout.splitlines()
            need(len(rows) == 1, 'Malformed request produced extra output')
            row = canonical(rows[0])
            need(type(row) is dict and set(row) == {'load_error', 'detail'} and
                 row['load_error'] == 'input_validation' and
                 b'candidate_must_not_load' not in result.stdout + result.stderr,
                 'Malformed packet reached candidate')
            control_rows.append({'kind': 'invalid-request', 'language': language,
                                 'name': item['name'], 'call_id': call, 'passed': True})
            call += 1
        for item in controls['invalid_results']:
            if language + '_source' not in item:
                continue
            cases = [{'args': [5]}]
            result, rows, _ = raw(call, language, item[language + '_source'], cases=cases,
                                  kind='invalid-result', name=item['name'])
            need(set(rows[0]) == {'i', 'error', 'detail'} and
                 rows[0]['error'] == 'candidate_or_output', 'Invalid result accepted')
            control_rows.append({'kind': 'invalid-result', 'language': language,
                                 'name': item['name'], 'call_id': call, 'passed': True})
            call += 1
    need(controls_summary == {'passed': True, 'calls': control_rows, 'sandbox_control_calls': 77,
                             'positive_cases': 32, 'host_control_checks': 49},
         'Control identities/counts differ')
    need(len(summary['rows']) == 2 and
         [r['language'] for r in summary['rows']] == ['python', 'javascript'],
         'Both language qualification transcripts required')
    totals = []
    for language_row in summary['rows']:
        language = language_row['language']
        extension = 'js' if language == 'javascript' else 'py'
        need(language_row['source_sha256'] == freeze['sources'][f'normalized/0868.{extension}'] and
             language_row['passed'] is True, 'Candidate source/status differs')
        chunks_seen = 0
        individuals = []
        for group in bound['host_tests']:
            allcases = group['tests']
            chunks = [r for r in language_row['chunks'] if r['group'] == group['name']]
            need(len(chunks) == (len(allcases)+3)//4, 'Missing test chunk')
            for position, chunk in enumerate(chunks):
                offset = 4*position
                cases = allcases[offset:offset+4]
                need(chunk['offset'] == offset and chunk['language'] == language and
                     type(chunk['call_id']) is int and chunk['call_id'] == call and
                     chunk == load(output / f'{language}-{group["name"]}-{offset}.json') and
                     chunk['raw_boundary_file'] == f'boundary-{call:05d}.json',
                     'Chunk/call identity differs')
                result, _, row = raw(call, language, cases=cases)
                call += 1
                decoded = decode(result.stdout, cases, language)
                verdict = score(result, decoded, cases)
                need(decoded == chunk['decoded_observations'] and chunk['transport_error'] is None and
                     chunk['protocol'] == row['protocol'] and chunk['sandbox_ok'] is True and
                     chunk['output_limit_exceeded'] is False and verdict == chunk['verdict'] and
                     verdict['passed'], 'Saved observation fails unchanged host judge')
                calculated = []
                for i, case in enumerate(cases):
                    one = score(result, [dict(decoded[i], i=0), {'done': 1}], [case])
                    need(one['passed'], 'Case failed unchanged comparison')
                    calculated.append({'case': offset+i, 'official_domain': 1 <= case['args'][0] <= 10**9,
                                       'passed': True, 'exact_argument_roundtrip': True,
                                       'runtime_types_valid': True})
                need(calculated == chunk['individual'], 'Per-case result/domain differs')
                individuals += calculated
                chunks_seen += 1
        need(chunks_seen == len(language_row['chunks']) == 18, 'Extra/unmatched chunks')
        totals.append({'cases': len(individuals), 'passed': sum(r['passed'] for r in individuals),
                       'official': sum(r['official_domain'] for r in individuals),
                       'extended': sum(not r['official_domain'] for r in individuals)})
    need(seen == set(range(1,115)) and call == 115, 'Missing/duplicate raw calls')
    need({Path(p).name for p in index if Path(p).parent == output and Path(p).name.startswith('boundary-')} ==
         {f'boundary-{i:05d}.json' for i in seen}, 'Extra indexed raw calls')
    for name in ['before.json', 'after.json']:
        proof(load(output / name))
    seal = load(output / 'execution-seal.json')
    need(seal == summary['seal'] and seal['runner_sha256'] == freeze['sources']['run.py'] and
         seal['freeze_sha256'] == ANCHORS['freeze'] and
         seal['runtime_contract_sha256'] == ANCHORS['runtime_contract'] and
         seal['toolchain_manifest_sha256'] == ANCHORS['toolchain_manifest'] and
         seal['approved_test_pins_sha256'] == freeze['sources']['approved-test-pins.json'] and
         seal['profile'] == PROFILE and seal['cpu_affinity'] == manifest['serial_cpu_affinity'] and
         seal['expected_outputs_in_sandbox'] is False and seal['frozen_before_independent_reload'] is True,
         'Execution seal differs')
    need(totals == [{'cases': 68, 'passed': 68, 'official': 52, 'extended': 16}]*2 and
         summary['controls_passed'] is True and summary['sandbox_control_calls'] == 77 and
         summary['boundary_records'] == 114 and summary['official_test_count'] == 52 and
         summary['all_unchanged_cases'] == 68 and summary['expected_outputs_in_sandbox'] is False and
         summary['technical_qualification_only'] is True and summary['admitted'] is False,
         'Qualification summary differs')
    return dict(totals[1], calls=114, control_calls=77)
