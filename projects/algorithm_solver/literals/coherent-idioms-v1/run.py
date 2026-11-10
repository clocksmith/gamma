"""Fit coherent exact literals on existing development IDs, then seal and audit.

All source materialization stays behind the hash-pinned KnownSpecService. Output
contains private literals/witnesses and must remain outside the repository.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import platform
import subprocess
from pathlib import Path
import statistics
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService
import coherent

PACKET_PATH = HERE.parent/'pass2/working/bitpack.py'
_spec = importlib.util.spec_from_file_location('coherent_literal_packet', PACKET_PATH)
PACKET = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PACKET)


def packet_for_complete(source, table, spans):
    literals = [entry['literal'] for entry in table['entries']]
    codes = [span['code'] for span in spans]
    if any(code is None for code in codes):
        raise ValueError('uncovered source cannot have a complete packet')
    dictionary = PACKET.dictionary_bytes(literals)
    packet = PACKET.encode(literals, codes, table['width'])
    if PACKET.decode(dictionary, packet) != source:
        raise ValueError('independent literal packet reconstruction failed')
    return dictionary, packet


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def packed(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def write(path, value):
    path.write_bytes(packed(value))


def materialize(service, ids, language, directory):
    records, membership = {}, []
    directory.mkdir()
    for pid in ids:
        key = str(pid)
        value = service.request('leetcode:' + key, language=language, include_source=True)
        artifact = value.get('artifact', {})
        impl = value.get('consumer_selection', {}).get('implementation', {})
        if artifact.get('status') != 'materialized':
            membership.append({'id':pid, 'status':'unavailable', 'reason':value.get('reason', value.get('status'))})
            continue
        source = artifact['source_utf8']
        raw = source.encode('utf-8')
        if impl.get('status') != 'qualified' or sha(raw) != impl['source_sha256']:
            raise ValueError('exact source qualification binding failed')
        records[key] = {'source':source, 'sha256':sha(raw), 'problem_id':'leetcode:' + key,
                        'qualification':{'status':'passed', 'source_sha256':sha(raw),
                            'receipt_sha256':impl['receipt_sha256'], 'contract':impl['problem_contract_sha256']}}
        (directory / (key + '.source')).write_bytes(raw)
        membership.append({'id':pid, 'status':'available', 'source_sha256':sha(raw),
            'receipt_sha256':impl['receipt_sha256'], 'runtime_sha256':impl['runtime_sha256'],
            'tests_sha256':impl['tests_sha256'], 'contract_scope':impl['contract_scope'],
            'caveats':impl['caveats']})
    return records, membership


def summarize(report, population):
    complete = [row for row in report['programs'].values() if row['complete']]
    selections = sorted(row['selections'] for row in complete)
    def measured_sum(field):
        values = [row.get(field) for row in complete]
        return sum(values) if all(type(value) is int and value >= 0 for value in values) else None
    return {'population':population, 'materialized_sources':report['total_programs'],
        'complete_programs':len(complete), 'unavailable_sources':population-report['total_programs'],
        'median_selections':statistics.median(selections) if selections else None,
        'p95_selections':selections[(95*len(selections)+99)//100-1] if selections else None,
        'uncovered_bytes':report['uncovered_bytes'],
        'selection_bits_on_complete_programs':sum(row['selection_bits'] for row in complete),
        'singleton_selection_bits_on_complete_programs':measured_sum('singleton_selection_bits'),
        'packet_bits_on_complete_programs':measured_sum('packet_bits'),
        'evidence_scope':'exact known-source representation, not unseen or autonomous solving'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--service', type=Path, required=True)
    parser.add_argument('--service-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--audit-all-authorized', action='store_true',
        help='After sealing, audit all service-authorized known IDs; no fitting on additional sources')
    args = parser.parse_args(argv)
    if args.output.resolve().is_relative_to(ROOT) or args.output.exists():
        raise ValueError('output must be a new private directory outside the repository')
    raw = args.service.read_bytes()
    if sha(raw) != args.service_sha256:
        raise ValueError('service hash mismatch')
    config = json.loads(raw)
    service = KnownSpecService.from_config(args.service.resolve(), args.service_sha256)
    partition_path = HERE.parent / 'cost-decomposition-v1/contract.json'
    partition = json.loads(partition_path.read_bytes())['partition']
    fit_ids, validation_ids = partition['dev_fit'], partition['dev_val']
    if len(fit_ids) != 300 or len(validation_ids) != 100 or set(fit_ids) & set(validation_ids):
        raise ValueError('historical development partition differs')
    authorized = config['source_access']['authorized_problem_ids']
    audit_ids = sorted(int(pid.removeprefix('leetcode:')) for pid in authorized) if args.audit_all_authorized else validation_ids
    if any(not pid.startswith('leetcode:') or not pid[9:].isascii() or not pid[9:].isdigit() for pid in authorized):
        raise ValueError('unsupported authorized source identity')
    code_paths = [path for path in HERE.iterdir() if path.suffix in ('.py','.cjs','.md')]
    code_paths += [HERE.parent/'macro-fragment-compare-v1/shapes.py',
        HERE.parent/'macro-fragment-compare-v1/js_shapes.cjs', PACKET_PATH, HERE.parent/'literals.py']
    code_paths += [ROOT/('projects/algorithm_solver/catalogue/'+name+'.py') for name in
        ('__init__','known_spec_service','catalogue','boundary_policy','materialize','retrieval')]
    for relative in ('projects/__init__.py','projects/algorithm_solver/__init__.py'):
        if (ROOT/relative).exists(): code_paths.append(ROOT/relative)
    pins = {str(path.relative_to(ROOT)):sha(path.read_bytes()) for path in code_paths}
    contract = {'schema':'gamma.coherent-idiom-development.v1', 'service_sha256':args.service_sha256,
        'partition_sha256':sha(partition_path.read_bytes()), 'fit_ids':fit_ids, 'validation_ids':validation_ids,
        'audit_ids':audit_ids, 'widths':[6,7,8], 'policy':'strict', 'code_pins':pins,
        'source_execution':False, 'source_publication':False, 'validation_fitting':False,
        'audit_scope':'known-source transfer; exposure is not established as fresh confirmation',
        'additional_source_fitting':False, 'fresh_native_qualification':False,
        'local_primitive_envelope_checks':True,
        'implementation_evidence':'archived code pins plus end-of-run drift check; execute from a separate frozen checkout',
        'runtime':{'python':platform.python_version(),
            'node':subprocess.run(['node','--version'],capture_output=True,text=True,check=True).stdout.strip()}}
    args.output.mkdir(parents=True)
    write(args.output/'contract.json', contract)
    for name in pins:
        target = args.output/'implementation'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT/name).read_bytes())
    summary = {'contract_sha256':sha(packed(contract)), 'status':'active', 'languages':{},
        'target_universe':4081, 'protected_sources_opened':0, 'fresh_native_qualifications':0}
    start = time.monotonic()
    for language in ('javascript','python'):
        folder = args.output/language; folder.mkdir()
        print(language, 'opening existing fit sources', flush=True)
        fit, fit_membership = materialize(service, fit_ids, language, folder/'fit-sources')
        if not fit: raise ValueError('no available fitting sources')
        candidates = [coherent.promote(c) for c in coherent.enumerate_candidates(fit, language)]
        tables = {str(width):coherent.select_table(candidates, language, width, records=fit)
                  for width in (6,7,8)}
        write(folder/'sealed-tables.json', tables)
        seal = sha(packed(tables))
        write(folder/'fit-membership.json', fit_membership)
        write(folder/'candidates.json', candidates)
        print(language, 'sealed', len(candidates), 'candidates', seal, flush=True)
        # No development-validation/additional-source read happens until sealing.
        audit, audit_membership = materialize(service, audit_ids, language, folder/'audit-sources')
        write(folder/'audit-membership.json', audit_membership)
        reports = {}
        for width, table in tables.items():
            report = coherent.evaluate_fixed_table(audit, table)
            reconstructed = 0
            packets = folder/('packets-'+width); packets.mkdir()
            dictionary_storage_bytes = None
            if table['entries']:
                dictionary = PACKET.dictionary_bytes([entry['literal'] for entry in table['entries']])
                (packets/'dictionary.bin').write_bytes(dictionary)
                dictionary_storage_bytes = len(dictionary)
            for key, row in report['programs'].items():
                raw = audit[key]['source'].encode()
                selected = [span for span in row['spans'] if span['code'] is not None]
                for span in selected:
                    text = table['entries'][span['code']]['literal'].encode()
                    if raw[span['start_byte']:span['end_byte']] != text:
                        raise ValueError('independent selected-span reconstruction failed')
                if len(selected) != row['selections']:
                    raise ValueError('selection accounting differs from replay')
                if row['complete']:
                    decoded = b''.join(table['entries'][span['code']]['literal'].encode() for span in selected)
                    if decoded != raw or row['selection_bits'] != len(selected)*int(width):
                        raise ValueError('independent full-source reconstruction failed')
                    dictionary, packet = packet_for_complete(audit[key]['source'], table, selected)
                    (packets/(key+'.bin')).write_bytes(packet)
                    (packets/'dictionary.bin').write_bytes(dictionary)
                    dictionary_storage_bytes = len(dictionary)
                    row.update(packet_bits=len(packet)*8, framing_bits=41*8,
                        padding_bits=(-row['selection_bits'])%8, packet_sha256=sha(packet))
                    reconstructed += 1
                else:
                    row['packet_bits'] = None
                # Preserve charged matches and uncovered ranges without a redundant
                # JSON object for each uncovered byte.
                row['spans'] = selected
                row['trace_scope'] = 'selected spans; uncovered byte ranges are explicit'
            report['independently_reconstructed_complete_sources'] = reconstructed
            write(folder/('audit-'+width+'.json'), report)
            reports[width] = summarize(report, len(audit_ids))
            reports[width]['entries'] = len(table['entries'])
            reports[width]['serialized_dictionary_bytes'] = dictionary_storage_bytes
            reports[width]['decoder_implementation_source_bytes'] = PACKET_PATH.stat().st_size + (HERE.parent/'literals.py').stat().st_size
            reports[width]['mapping_sha256'] = table['mapping_sha256']
            validation_rows = {key:row for key,row in report['programs'].items() if int(key) in validation_ids}
            validation = dict(report, programs=validation_rows, total_programs=len(validation_rows),
                              uncovered_bytes=sum(row['uncovered_bytes'] for row in validation_rows.values()))
            reports[width]['exposed_validation'] = summarize(validation, len(validation_ids))
            print(language, width, 'complete', reports[width]['complete_programs'], '/', len(audit_ids), flush=True)
        summary['languages'][language] = {'fit_population':len(fit_ids), 'fit_materialized':len(fit),
            'candidate_states':dict(Counter(c['state'] for c in candidates)),
            'candidate_families':dict(Counter(c['kind'] for c in candidates)),
            'seal_sha256':seal, 'widths':reports}
        write(args.output/'summary.json', summary)
    if any(sha((ROOT/name).read_bytes()) != digest for name,digest in pins.items()):
        raise ValueError('implementation changed during the run')
    summary.update(status='completed', elapsed_seconds=time.monotonic()-start)
    write(args.output/'summary.json', summary)
    print('completed', args.output/'summary.json', flush=True)


if __name__ == '__main__':
    main()
