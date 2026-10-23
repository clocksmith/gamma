"""Independently replay private artifacts; emit explicitly selected metadata only."""
import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path.insert(0, str(HERE))
import implicit
sys.path.insert(0, str(LIT/'fraction-capacity-v1'))
import dual
analyze = dual.analyze

PROOF = 'binding-descent-v1/evidence/results.json'
REUSE = 'not_performed_relaxation_witness_only'
STOPS = {'iteration_limit', 'time_limit', 'restricted_dual_stationary',
         'exact_primal_optimum_certificate'}


def integer(value, minimum=None):
    assert type(value) is int and (minimum is None or value >= minimum)
    return value


def seconds(value):
    assert type(value) in (int, float) and math.isfinite(value) and value >= 0
    return value


def guard():
    if not __debug__ or sys.flags.optimize or os.environ.get('PYTHONOPTIMIZE') not in (None, '', '0'):
        raise RuntimeError('report validation requires assertions')


def exact_packet_ids(packet, dictionary, vocab, text):
    """Independent eight-bit header/ID parsing, followed by source reconstruction."""
    assert packet[:5] == b'LTV1\x08' and len(packet) >= 41
    assert packet[5:37].hex() == analyze.sha(dictionary)
    count = int.from_bytes(packet[37:41], 'big')
    ids = list(packet[41:])
    assert len(ids) == count and all(entry < len(vocab) for entry in ids)
    assert ''.join(vocab[entry] for entry in ids) == text
    assert analyze.decode(dictionary, packet) == text
    return ids


def witness(private, raw, texts, banned, c, lower_bound):
    vocab = json.loads((private/'dictionary.json').read_text())
    assert isinstance(vocab, list) and all(type(word) is str and word for word in vocab)
    assert 0 < len(vocab) == len(set(vocab)) <= c['pool']['capacity']
    assert not set(vocab) & banned
    dictionary = (private/'dictionary.bin').read_bytes()
    assert dictionary == analyze.dictionary_bytes(vocab)
    assert analyze.sha((private/'dictionary.json').read_bytes()) == raw['dictionary_sha256']
    assert set(raw['per_problem']) == set(texts)
    uses, used_by = Counter(), [set() for _ in vocab]
    rows = {}
    for pid, text in sorted(texts.items()):
        original = raw['per_problem'][pid]
        packet = (private/'packets'/f'{pid}.bin').read_bytes()
        ids = exact_packet_ids(packet, dictionary, vocab, text)
        objective, expected_ids = dual.encode_objective(text, vocab)
        assert ids == expected_ids and packet == analyze.encode(vocab, expected_ids, 8)
        characters = sum(len(vocab[entry]) == 1 for entry in ids)
        row = {'source_sha256': analyze.sha(text.encode()), 'selections': len(ids),
               'actions': len(ids)+1, 'characters': characters,
               'objective': 10*characters-len(ids), 'packet_bytes': len(packet),
               'packet_sha256': analyze.sha(packet),
               'one_program_package_bytes': len(dictionary)+len(packet),
               'one_program_with_decoder': len(dictionary)+len(packet)+c['decoder_dependency_bytes']}
        assert objective == row['objective']
        for key, value in row.items():
            assert original[key] == value, (pid, key)
        rows[pid] = row
        uses.update(ids)
        for entry in set(ids):
            used_by[entry].add(pid)
    entry_stats = []
    for entry, word in enumerate(vocab):
        # Recompute support directly from source membership, independently of
        # the production suffix intervals. No actual entry string is emitted.
        owners = [pid for pid, text in texts.items() if word in text]
        assert owners
        entry_stats.append({'entry_id': entry, 'characters': len(word),
                            'utf8_bytes': len(word.encode()),
                            'distinct_program_support': len(owners),
                            'packet_program_use': len(used_by[entry]),
                            'selection_uses': uses[entry],
                            'maximum_fraction_of_containing_source':
                                max(len(word)/len(texts[pid]) for pid in owners)})
    selections = analyze.distribution([row['selections'] for row in rows.values()])
    characters = sum(row['characters'] for row in rows.values())
    package = len(dictionary)+sum(row['packet_bytes'] for row in rows.values())
    clean = {'per_problem': rows, 'selections': selections,
             'actions': analyze.distribution([row['actions'] for row in rows.values()]),
             'characters': characters, 'character_fraction': characters/selections['total'],
             'objective': 10*characters-selections['total'], 'entries': len(vocab),
             'character_entries': sum(len(word) == 1 for word in vocab),
             'dictionary_sha256': analyze.sha((private/'dictionary.json').read_bytes()),
             'dictionary_bytes': len(dictionary), 'package_bytes': package,
             'package_with_decoder_sources': package+c['decoder_dependency_bytes'],
             'amortized_package_bytes': package/len(texts), 'framing_bytes': 41*len(texts),
             'payload_bits': 8*selections['total'], 'padding_bits': 0,
             'one_owner_entries': sum(row['distinct_program_support'] == 1 for row in entry_stats),
             'maximum_entry_length': max(map(len, vocab)), 'semantic_reuse_audit': REUSE}
    for key, value in clean.items():
        assert raw[key] == value, key
    assert clean['objective'] == sum(row['objective'] for row in rows.values()) >= lower_bound
    clean.update(entry_statistics=entry_stats,
                 minimum_entry_length=min(map(len, vocab)),
                 median_entry_length=statistics.median(map(len, vocab)),
                 entries_covering_at_least_90_percent_of_a_source=sum(
                     row['maximum_fraction_of_containing_source'] >= .9 for row in entry_stats),
                 unused_entries=sum(row['selection_uses'] == 0 for row in entry_stats),
                 ten_percent_witness=clean['objective'] <= 0,
                 exact_packet_ids_and_costs_rechecked=True)
    return clean, vocab


def replay_arm(raw, folder, work, c, contract_hash, qualification):
    cohort = raw['cohort']
    assert cohort in ('R', 'naming') and raw['mode'] == 'flex256'
    assert raw['complete'] is True and raw['validation_loaded'] is False
    assert raw['contract_sha256'] == contract_hash
    assert raw['capacity'] == c['pool']['capacity'] == 256 and raw['mandatory_entries'] == 0
    assert raw['pool_scope'] == c['pool']['scope']
    private = folder/f'{cohort}-flex256'
    assert json.loads((private/'results.json').read_text()) == raw
    rel = c['cohorts'][cohort]
    texts = json.loads((work/rel/'fit-sources.json').read_text())
    assert set(texts) == {str(pid) for pid in c['fit_ids']}
    assert len(texts) == raw['fit_problems'] == 300
    assert all(type(text) is str and text for text in texts.values())
    assert set(''.join(texts.values())) <= set(dual.ALPHABET)
    assert raw['fit_source_sha256'] == c['private_files'][rel+'/fit-sources.json']
    receipts = [row for row in qualification['arms']
                if row['arm'] == ('control' if cohort == 'R' else 'scope_joint') and row['width'] == 8]
    assert len(receipts) == 1
    receipt = receipts[0]
    for pid, text in texts.items():
        assert analyze.sha(text.encode()) == receipt['per_problem'][pid]['source_sha256']
        assert receipt['qualification'][pid]['passed'] is True
    banned = dual.sel.forbidden_strings(texts)
    index = implicit.Index(texts, banned)
    count_metadata = {'pool_entries': index.distinct_allowed_entries,
                      'implicit_groups': len(index.groups), 'source_characters': len(index.positions),
                      'exact_ban_occurrences': sum(len(ends) for rows in index.banned_ends.values() for ends in rows),
                      'maximum_entry_length_upper_bound': max(map(len, texts.values()))}
    for key, value in count_metadata.items():
        assert raw[key] == value, key
    optimization = raw['optimization']
    cert = optimization['certificate']
    q_path = private/'certificate-q.json'
    assert analyze.sha(q_path.read_bytes()) == cert['q_sha256']
    q = json.loads(q_path.read_text())
    denominator = integer(cert['denominator'], 1)
    assert denominator == c['search']['denominator']
    numerator = implicit.verify(index, q, 256, denominator)
    rebuilt = index.certificate(q, 256, denominator)
    assert numerator == rebuilt['numerator'] == integer(cert['numerator'])
    for key in ('path_numerators', 'top_capacity_numerator', 'integer_lower_bound'):
        assert cert[key] == rebuilt[key], key
    assert sum(cert['path_numerators'].values())-cert['top_capacity_numerator'] == numerator
    assert cert['independent_partition_and_integer_replay'] is True
    assert cert['excludes_ten_percent'] == (rebuilt['integer_lower_bound'] > 0)
    lower = rebuilt['integer_lower_bound']
    clean_cert = {key: rebuilt[key] for key in ('numerator', 'denominator', 'integer_lower_bound',
                                               'path_numerators', 'top_capacity_numerator')}
    clean_cert.update(q_sha256=cert['q_sha256'], independent_partition_and_integer_replay=True,
                      excludes_ten_percent=lower > 0)
    assert {'seed', 'best'} <= set(raw['witnesses']) <= {'seed', 'best', 'generated'}
    witnesses, vocabs = {}, {}
    for name, values in raw['witnesses'].items():
        witnesses[name], vocabs[name] = witness(private/name, values, texts, banned, c, lower)
    pinned_seed = json.loads((work/rel/'dictionary.json').read_text())
    assert len(pinned_seed) == len(set(pinned_seed)) <= 256 and not set(pinned_seed) & banned
    expected_seed = [word for word in pinned_seed if any(word in text for text in texts.values())]
    assert vocabs['seed'] == expected_seed
    assert optimization['seed_objective'] == witnesses['seed']['objective']
    assert optimization['best_objective'] == witnesses['best']['objective']
    assert optimization['generated_objective'] == (witnesses['generated']['objective'] if 'generated' in witnesses else None)
    assert witnesses['best']['objective'] == min(row['objective'] for row in witnesses.values())
    iterations = integer(optimization['iterations'], 1)
    assert iterations <= c['search']['iterations']
    assert optimization['stop'] in STOPS
    if optimization['stop'] == 'iteration_limit':
        assert iterations == c['search']['iterations']
    if optimization['stop'] == 'time_limit':
        assert seconds(optimization['seconds']) >= c['search']['seconds']
    if optimization['stop'] == 'exact_primal_optimum_certificate':
        assert lower == witnesses['best']['objective']
    attempts = integer(optimization['primal_attempts'], 0)
    infeasible = integer(optimization['primal_infeasible'], 0)
    assert infeasible <= attempts == 2*((iterations-1)//c['search']['primal_every']+1)
    assert ('generated' in witnesses) == (attempts > infeasible)
    traces = [json.loads(line) for line in (private/'trace.jsonl').read_text().splitlines()]
    assert len(traces) == iterations
    best = None
    for iteration, row in enumerate(traces):
        assert row['iteration'] == iteration and row['validation_loaded'] is False
        exact = integer(row['exact_numerator'])
        best = exact if best is None else max(best, exact)
        assert row['integer_lower_bound'] == -(-exact//denominator)
        assert row['best_integer_lower_bound'] == -(-best//denominator)
    assert best == numerator
    assert traces[-1]['upper_bound'] == witnesses['best']['objective']
    assert traces[-1]['generated_objective'] == optimization['generated_objective']
    clean_optimization = {'certificate': clean_cert, 'iterations': iterations,
                          'stop': optimization['stop'], 'primal_attempts': attempts,
                          'primal_infeasible': infeasible,
                          'seed_objective': witnesses['seed']['objective'],
                          'best_objective': witnesses['best']['objective'],
                          'generated_objective': optimization['generated_objective'],
                          'seconds': seconds(optimization['seconds'])}
    return {'cohort': cohort, 'mode': 'flex256', 'fit_problems': len(texts),
            'validation_loaded': False, 'complete': True, 'capacity': 256,
            'mandatory_entries': 0, **count_metadata,
            'pool_seconds': seconds(raw['pool_seconds']), 'seconds': seconds(raw['seconds']),
            'fit_source_sha256': raw['fit_source_sha256'], 'optimization': clean_optimization,
            'witnesses': witnesses, 'qualification_source_hashes_rechecked': True,
            'index_bans_and_full_pool_partition_rebuilt': True,
            'certificate_replayed': True, 'semantic_reuse_audit': REUSE}


def build_report(folder, work, here=HERE, lit=LIT):
    guard()
    c_path = here/'contract.json'
    c = json.loads(c_path.read_text())
    contract_hash = analyze.sha(c_path.read_bytes())
    for rel, digest in c['code_hashes'].items():
        assert analyze.sha((lit/rel).read_bytes()) == digest, rel
    for path, digest in c['runtime_files'].items():
        assert analyze.sha(Path(path).read_bytes()) == digest, path
    base = {'schema': 'gamma.all-substring-fraction.report.v1', 'contract_sha256': contract_hash,
            'validation_loaded': False, 'inherited_item23_failure_retained':
                'Later unchanged-source qualification exited 137; this exact item 13 hash reuse does not erase that failure.',
            'semantic_reuse_audit': REUSE}
    # Failure dominates a stale or partially written aggregate. No source input
    # is needed or opened to report a failed whole job.
    if (folder/'failure.json').exists():
        failure_path = folder/'failure.json'
        failure = json.loads(failure_path.read_text())
        assert failure['contract_sha256'] == contract_hash
        assert failure['complete'] is False and failure['partial_certificates_promoted'] is False
        assert failure['validation_loaded'] is False
        exception = failure['exception']
        allowed = {'TimeoutError', 'MemoryError', 'AssertionError', 'RuntimeError', 'ValueError',
                   'FileNotFoundError', 'OSError', 'KeyboardInterrupt', 'SystemExit'}
        return {**base, 'complete': False, 'status': 'incomplete; no whole-job certificate accepted',
                'failure_sha256': analyze.sha(failure_path.read_bytes()),
                'failure': {'exception': exception if exception in allowed else 'other_exception',
                            'seconds': seconds(failure['seconds']), 'partial_certificates_promoted': False},
                'predictions': {'P1': False, 'P2': None, 'P3': None}}
    raw_path = folder/'results.json'
    raw = json.loads(raw_path.read_text())
    assert raw['complete'] is True and raw['validation_loaded'] is False
    assert raw['contract_sha256'] == contract_hash
    assert {row['cohort'] for row in raw['arms']} == {'R', 'naming'} and len(raw['arms']) == 2
    for rel, digest in c['private_files'].items():
        assert analyze.sha((work/rel).read_bytes()) == digest, rel
    qualification_path = lit/PROOF
    assert PROOF in c['code_hashes']
    assert analyze.sha(qualification_path.read_bytes()) == c['code_hashes'][PROOF]
    qualification = json.loads(qualification_path.read_text())
    arms = [replay_arm(row, folder, work, c, contract_hash, qualification)
            for row in sorted(raw['arms'], key=lambda row: row['cohort'])]
    elapsed = seconds(raw['seconds'])
    assert elapsed <= c['limits']['overall_seconds']
    assert all(arm['seconds'] <= elapsed for arm in arms)
    return {**base, 'complete': True, 'status': 'complete; independently replayed', 'arms': arms,
            'seconds': elapsed, 'private_results_sha256': analyze.sha(raw_path.read_bytes()),
            'qualification_receipt_sha256': c['code_hashes'][PROOF],
            'decoder_dependency_bytes': c['decoder_dependency_bytes'],
            'offline_encoder_bytes': c['offline_encoder_bytes'],
            'offline_encoder_scope': 'Conservative inherited source/parser inventory; full installed runtime footprint remains unmeasured.',
            'decoded_packets': sum(len(w['per_problem']) for arm in arms for w in arm['witnesses'].values()),
            'predictions': {'P1': True,
                            'P2': any(arm['optimization']['certificate']['excludes_ten_percent'] for arm in arms),
                            'P3': all(not arm['witnesses'].get('generated', {}).get('ten_percent_witness', False) for arm in arms)}}


def markdown(result):
    lines = ['# Full-substring character-fraction certificate', '',
             '[Freeze](FREEZE.md); [resource amendment](AMENDMENT-1.md); [review](REVIEW.md); [derivation](DRAFT.md); [metadata evidence](evidence/results.json).', '',
             'Private sources, substring pools, multipliers, dictionaries and packet sequences are not published.', '']
    if not result['complete']:
        failure = result['failure']
        lines += [f'The whole job failed with {failure["exception"]} after {failure["seconds"]:.2f} seconds. '
                  'No complete experiment certificate or partial worker result is accepted. '
                  'P1 is false; P2 and P3 remain unevaluated. Failure reporting opens no source inputs.', '']
    else:
        arms = result['arms']
        positive = [arm['cohort'] for arm in arms if arm['optimization']['certificate']['excludes_ten_percent']]
        if positive:
            lines += ['A positive independently replayed integer bound excludes a 10% character fraction '
                      'for the complete fixed 300-program fit population in: '+', '.join(positive)+'.', '']
        else:
            lines += ['Neither start-tied certificate is positive. The full-substring fraction question '
                      'remains unresolved unless an exact decoded witness below reaches F <= 0.', '']
        lines += ['The objective is F = 10C - T, where C counts single-character selections and T counts '
                  'all eight-bit selections. The candidate class contains every occurring nonempty exact '
                  'substring at every length, including one-owner entries, except exact fit source/body '
                  'bans. Every entry consumes one of 256 optional dictionary slots.', '',
                  '| Cohort | Distinct words / groups | Exact numerator / denominator | Integer bound | Best feasible F | Excludes 10% | Iterations / stop |',
                  '| --- | ---: | --- | ---: | ---: | --- | --- |']
        for arm in arms:
            opt = arm['optimization']; cert = opt['certificate']
            lines.append(f'| {arm["cohort"]} | {arm["pool_entries"]:,} / {arm["implicit_groups"]:,} | '
                         f'{cert["numerator"]} / {cert["denominator"]} | {cert["integer_lower_bound"]} | '
                         f'{opt["best_objective"]} | {cert["excludes_ten_percent"]} | '
                         f'{opt["iterations"]} / {opt["stop"]} |')
        lines += ['', 'The full primal substring space is covered, but the dual search ties all '
                  'multipliers at a source start. Long one-owner suffix groups contain many lengths '
                  'with the same activation weight; top-256 subtraction can spend many activations '
                  'on those same starts. A nonpositive bound may reflect this restricted dual family. '
                  'It does not prove that an actual dictionary reaches the target or that the full '
                  'substring representation has failed. A positive bound remains valid for all '
                  'dictionaries and segmentations in the stated fixed-source class.', '',
                  '| Cohort | Witness | Entries / one-owner | Selections | Median / p90 / p95 / worst | Character fraction | F | Package / with decoder source bytes |',
                  '| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |']
        for arm in arms:
            for name, row in arm['witnesses'].items():
                s = row['selections']
                lines.append(f'| {arm["cohort"]} | {name} | {row["entries"]} / {row["one_owner_entries"]} | '
                             f'{s["total"]} | {s["median"]} / {s["p90"]} / {s["p95"]} / {s["worst"]} | '
                             f'{100*row["character_fraction"]:.2f}% | {row["objective"]} | '
                             f'{row["package_bytes"]} / {row["package_with_decoder_sources"]} |')
        lines += ['', 'Every witness packet was independently parsed into eight-bit IDs, reconstructed, '
                  'matched to the exact min-F encoder and qualified source hash, and fully recounted. '
                  'The encoder minimizes F, then selection count and dictionary IDs; this is not '
                  'minimum-ratio or minimum-selection encoding. Costs include one Finish action, '
                  '41 framing bytes per program, dictionary bytes and decoder source bytes. Evidence '
                  'contains per-program costs, entry lengths, distinct-program support and actual '
                  'packet usage, without entry strings.', '',
                  '| Cohort | Witness | Min / median / max entry length | Entries >=90% of a containing source | Unused entries | Character entries |',
                  '| --- | --- | --- | ---: | ---: | ---: |']
        for arm in arms:
            for name, row in arm['witnesses'].items():
                lines.append(f'| {arm["cohort"]} | {name} | {row["minimum_entry_length"]} / '
                             f'{row["median_entry_length"]} / {row["maximum_entry_length"]} | '
                             f'{row["entries_covering_at_least_90_percent_of_a_source"]} | '
                             f'{row["unused_entries"]} | {row["character_entries"]} |')
        lines += ['', 'The 90% size statistic describes near-whole entries; it is not a semantic legality '
                  'test. Exact bans can still admit near-whole or disguised task-specific chunks. '
                  'All witnesses remain relaxation witnesses with semantic reuse unassessed. Even an '
                  'F <= 0 witness does not establish M1 reusable-library legality, quantile targets, '
                  '400-of-500 coverage, source-rewriting limits, human fluency or autonomous solving.', '',
                  '| Cohort | Proposals / infeasible | Pool construction / ascent and replay / total arm seconds |',
                  '| --- | ---: | --- |']
        for arm in arms:
            opt = arm['optimization']
            lines.append(f'| {arm["cohort"]} | {opt["primal_attempts"]} / {opt["primal_infeasible"]} | '
                         f'{arm["pool_seconds"]:.2f} / {opt["seconds"]:.2f} / {arm["seconds"]:.2f} |')
        lines += ['', f'{result["decoded_packets"]} witness packets replayed; whole-job wall time '
                  f'{result["seconds"]:.2f} seconds. The report reconstructs the suffix index and exact '
                  'bans, verifies full interval/depth coverage, and checks exact integer path/top-256 '
                  'accounting using independent partition validation and segment-tree replay. '
                  'No optimizer is run by this reporter.', '']
    lines += ['| Prediction | Definition | Met |', '| --- | --- | --- |']
    definitions = {'P1': 'Both arms complete a verified certificate within hard caps',
                   'P2': 'At least one positive bound (low-confidence hypothesis)',
                   'P3': 'Neither generated dictionary reaches F <= 0'}
    for key, definition in definitions.items():
        value = result['predictions'][key]
        lines.append(f'| {key} | {definition} | {"unevaluated" if value is None else value} |')
    lines += ['', result['inherited_item23_failure_retained'], '',
              'Qualification here reuses exact item 13 source hashes. It does not replace that failure '
              'with a new runtime receipt. Validation and protected source values remain unopened. '
              'The complete installed interpreter/library footprint is unmeasured. Component intent '
              'and production boundaries are unchanged; no promotion or milestone readiness is claimed.', '',
              'Rebuild using the pinned Python with `report.py --run /private/all-substring-fraction/run-v1 '
              '--work /private/literal-admission500-v1`. Synthetic reporter checks are available with '
              '`report.py --self-test`.', '']
    return '\n'.join(lines)


def write_report(result, here=HERE):
    # Build/verify everything before either public artifact is replaced.
    document = markdown(result)
    serialized = json.dumps(result, sort_keys=True, indent=2)+'\n'
    (here/'evidence').mkdir(exist_ok=True)
    for path, content in ((here/'evidence/results.json', serialized), (here/'README.md', document)):
        temporary = path.with_suffix(path.suffix+'.tmp')
        temporary.write_text(content)
        temporary.replace(path)


def main(folder, work):
    result = build_report(folder, work)
    write_report(result)
    return result


def self_test():
    """Full synthetic 300+300 fixtures; never opens any real private input."""
    import copy
    import importlib.util
    import tempfile
    import optimize
    spec = importlib.util.spec_from_file_location('synthetic_packet_writer', LIT/'all-length-fraction-v1/run.py')
    writer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(writer)
    with tempfile.TemporaryDirectory(prefix='gamma-substring-report-synthetic-') as temporary:
        base = Path(temporary); here = base/'report'; lit = base/'lit'; work = base/'work'; folder = base/'run'
        for path in (here, lit, work, folder):
            path.mkdir()
        texts = {str(pid): 'function solve(a){return a+1;}' for pid in range(300)}
        seed = sorted(set(next(iter(texts.values()))))+['~']
        proof_path = lit/PROOF; proof_path.parent.mkdir(parents=True)
        qualification = {'arms': [{'arm': name, 'width': 8,
                                   'per_problem': {pid: {'source_sha256': analyze.sha(text.encode())} for pid, text in texts.items()},
                                   'qualification': {pid: {'passed': True} for pid in texts}}
                                  for name in ('control', 'scope_joint')]}
        analyze.write(proof_path, qualification)
        c = {'fit_ids': list(range(300)), 'cohorts': {'R': 'R', 'naming': 'naming'},
             'code_hashes': {PROOF: analyze.sha(proof_path.read_bytes())}, 'runtime_files': {},
             'private_files': {}, 'decoder_dependency_bytes': 13010, 'offline_encoder_bytes': 12345,
             'pool': {'capacity': 256, 'scope': 'synthetic all-substring fixture'},
             'search': {'iterations': 1, 'seconds': 10, 'denominator': 1000, 'halve_after': 30, 'primal_every': 25},
             'limits': {'overall_seconds': 2400}}
        for cohort in c['cohorts']:
            (work/cohort).mkdir()
            for name, value in (('fit-sources.json', texts), ('dictionary.json', seed)):
                path = work/cohort/name; analyze.write(path, value)
                c['private_files'][f'{cohort}/{name}'] = analyze.sha(path.read_bytes())
        analyze.write(here/'contract.json', c)
        contract_hash = analyze.sha((here/'contract.json').read_bytes())
        arms = []
        for cohort in c['cohorts']:
            private = folder/f'{cohort}-flex256'; private.mkdir()
            banned = dual.sel.forbidden_strings(texts)
            index = implicit.Index(texts, banned)
            trace = []
            info, q, clean_seed, best, generated = optimize.optimize(index, seed, 256, c['search'], trace.append)
            for row in trace:
                row['validation_loaded'] = False
            (private/'trace.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in trace))
            analyze.write(private/'certificate-q.json', q)
            info['certificate']['q_sha256'] = analyze.sha((private/'certificate-q.json').read_bytes())
            witnesses = {}
            for name, vocab in (('seed', clean_seed), ('best', best), ('generated', generated)):
                if vocab is None:
                    continue
                row = writer.measure(texts, vocab, private/name, c['decoder_dependency_bytes'])
                row.update(one_owner_entries=0, maximum_entry_length=max(map(len, vocab)), semantic_reuse_audit=REUSE)
                witnesses[name] = row
            arm = {'cohort': cohort, 'mode': 'flex256', 'fit_problems': 300, 'validation_loaded': False,
                   'complete': True, 'contract_sha256': contract_hash, 'pool_scope': c['pool']['scope'],
                   'capacity': 256, 'mandatory_entries': 0, 'pool_entries': index.distinct_allowed_entries,
                   'implicit_groups': len(index.groups), 'source_characters': len(index.positions),
                   'exact_ban_occurrences': sum(len(ends) for rows in index.banned_ends.values() for ends in rows),
                   'maximum_entry_length_upper_bound': max(map(len, texts.values())),
                   'pool_seconds': 0., 'seconds': 10., 'optimization': info, 'witnesses': witnesses,
                   'fit_source_sha256': c['private_files'][cohort+'/fit-sources.json'],
                   'ignored_raw_payload': 'NEVER_EXPORT_SOURCE_PAYLOAD'}
            analyze.write(private/'results.json', arm); arms.append(arm)
        aggregate = {'arms': arms, 'complete': True, 'validation_loaded': False,
                     'contract_sha256': contract_hash, 'seconds': 20.}
        analyze.write(folder/'results.json', aggregate)
        result = build_report(folder, work, here, lit)
        write_report(result, here)
        assert result['complete'] and result['decoded_packets'] >= 1200
        serialized = (here/'evidence/results.json').read_text()
        assert 'NEVER_EXPORT_SOURCE_PAYLOAD' not in serialized
        assert next(iter(texts.values())) not in serialized
        assert not {'q', 'vocab', 'sources', 'pool'} & set(result)
        width = None
        for line in (here/'README.md').read_text().splitlines():
            if line.startswith('|'):
                current = len(line.split('|'))
                assert width is None or current == width
                width = current
            else:
                width = None
        checks = 1

        def rejects(callback):
            nonlocal checks
            try:
                callback()
            except (AssertionError, ValueError):
                checks += 1
            else:
                raise AssertionError('corrupted synthetic result accepted')

        # Arbitrary payload ID corruption must fail before any evidence write.
        packet_path = folder/'R-flex256/seed/packets/0.bin'
        saved = packet_path.read_bytes()
        packet_path.write_bytes(saved[:-1]+b'\xff')
        rejects(lambda: build_report(folder, work, here, lit))
        packet_path.write_bytes(saved)
        baseline_public = (here/'evidence/results.json').read_bytes()

        def corrupt_arm(change):
            mutated = copy.deepcopy(aggregate)
            change(mutated['arms'][0])
            analyze.write(folder/'R-flex256/results.json', mutated['arms'][0])
            analyze.write(folder/'results.json', mutated)
            rejects(lambda: build_report(folder, work, here, lit))
            analyze.write(folder/'R-flex256/results.json', aggregate['arms'][0])
            analyze.write(folder/'results.json', aggregate)
            assert (here/'evidence/results.json').read_bytes() == baseline_public

        corrupt_arm(lambda arm: arm.__setitem__('pool_entries', arm['pool_entries']+1))
        corrupt_arm(lambda arm: arm['witnesses']['best'].__setitem__('one_owner_entries', 1))
        corrupt_arm(lambda arm: arm['witnesses']['best'].__setitem__('maximum_entry_length', 999))
        corrupt_arm(lambda arm: arm['witnesses']['best']['per_problem']['0'].__setitem__('characters', 999))
        corrupt_arm(lambda arm: arm['optimization']['certificate']['path_numerators'].__setitem__('0', 999))
        # Even a refreshed q file hash cannot make a different exact bound pass.
        q_path = folder/'R-flex256/certificate-q.json'; saved_q = q_path.read_bytes()
        altered = json.loads(saved_q); altered['0'][0] += 1000; analyze.write(q_path, altered)
        corrupt_arm(lambda arm: arm['optimization']['certificate'].__setitem__('q_sha256', analyze.sha(q_path.read_bytes())))
        q_path.write_bytes(saved_q)
        # Re-pin a deliberately wrong synthetic qualification receipt to ensure
        # source identity is checked beyond the receipt file's own hash.
        saved_proof = proof_path.read_bytes(); saved_contract = (here/'contract.json').read_bytes()
        bad_proof = copy.deepcopy(qualification)
        bad_proof['arms'][0]['per_problem']['0']['source_sha256'] = '0'*64
        analyze.write(proof_path, bad_proof)
        bad_contract = copy.deepcopy(c); bad_contract['code_hashes'][PROOF] = analyze.sha(proof_path.read_bytes())
        analyze.write(here/'contract.json', bad_contract)
        updated_hash = analyze.sha((here/'contract.json').read_bytes())
        changed = copy.deepcopy(aggregate); changed['contract_sha256'] = updated_hash
        for arm in changed['arms']:
            arm['contract_sha256'] = updated_hash
            analyze.write(folder/f'{arm["cohort"]}-flex256/results.json', arm)
        analyze.write(folder/'results.json', changed)
        rejects(lambda: build_report(folder, work, here, lit))
        proof_path.write_bytes(saved_proof); (here/'contract.json').write_bytes(saved_contract)
        for arm in aggregate['arms']:
            analyze.write(folder/f'{arm["cohort"]}-flex256/results.json', arm)
        analyze.write(folder/'results.json', aggregate)
        # Failure takes precedence even if an aggregate exists, and succeeds
        # with a nonexistent work root: failure reporting reads no private input.
        failure = {'contract_sha256': contract_hash, 'complete': False, 'validation_loaded': False,
                   'partial_certificates_promoted': False, 'exception': 'TimeoutError', 'seconds': 2400.1}
        analyze.write(folder/'failure.json', failure)
        incomplete = build_report(folder, base/'nonexistent-private-input', here, lit)
        assert not incomplete['complete'] and 'arms' not in incomplete
        assert incomplete['predictions'] == {'P1': False, 'P2': None, 'P3': None}
        write_report(incomplete, here)
        checks += 1
        failure['contract_sha256'] = '0'*64; analyze.write(folder/'failure.json', failure)
        rejects(lambda: build_report(folder, base/'nonexistent-private-input', here, lit))
        return {'synthetic_report_checks': checks, 'decoded_fixture_packets': result['decoded_packets'],
                'private_corpus_opened': False, 'complete_failure_and_corruption_checks': 'passed'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path)
    parser.add_argument('--work', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
    else:
        if args.run is None or args.work is None:
            parser.error('--run and --work are required unless --self-test is used')
        main(args.run, args.work)
