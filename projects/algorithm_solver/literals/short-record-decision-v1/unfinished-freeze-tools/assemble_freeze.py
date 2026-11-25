#!/usr/bin/env python3
# UNFINISHED. Part of a short-record-decision freeze that was paused before FREEZE.json was written.
# Nothing here is pinned. See ../FREEZE-PROGRESS.md for what was run, what was never run, and the next steps.
"""Assemble FREEZE.json from the freeze owner's measurements.

    python3 -B assemble_freeze.py --tuning w1-short-files=T1.json --tuning w2-message-entries=T2.json \
        --tuning w3-commit-subjects=T3.json --explore-log tried.jsonl --fidelity adapter-fidelity-old-suites.json \
        --started-utc 2026-11-25T13:38:07Z --frozen-utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --out FREEZE.json --tuning-table-out baseline-tuning-validation.json

Nothing is decided here by hand:

  baselines   per method and workload, the setting ranked first by `tune_baselines.py`
              (smallest model bytes + stored validation bytes; ties: smaller model, earlier grid position)
  candidate   per workload, the configuration in the log of `explore_candidate.py` with the smallest
              all-in validation bytes among those that ran and reconstructed every validation record
              in both readers (ties: fewer dictionary entries, then earlier in the log)

The fixed parts (gate numbers, index form, timing rule) are the constants at the top of this file;
the gate numbers are copied from PREREGISTRATION.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bits_adapter as A  # noqa: E402
import freeze_common as F  # noqa: E402
import score as SCORE  # noqa: E402

PER_RECORD_ORDER = ['raw-indexed', 'zstd-raw-block-tuned', 'zstd-lean-frame-tuned', 'deflate-raw-tuned', 'fsst-reference']
BLOCKS_ORDER = ['zstd-lean-frame-blocks-of-2', 'zstd-lean-frame-blocks-of-4', 'zstd-lean-frame-blocks-of-8',
                'zstd-lean-frame-blocks-of-16']
ROLES = {'w1-short-files': 'decision', 'w2-message-entries': 'decision', 'w3-commit-subjects': 'spare'}
FSST_COMMIT = 'e638d4cf8c26129d73c242a4127b42b975de5b63'

HARNESS_SETTINGS = {'folds': 4, 'seed': 1, 'grid': 'full', 'block_sizes': [2, 4, 8, 16]}

BYTE_ACCOUNTING = {
    'total_bytes': 'the length of one serialised, self-contained archive of the scored records, from which a reader given '
                   'nothing else returns any one record',
    'counted_parts': {
        'header': 'the container header (16 bytes for the harness container, 9 for BIT3)',
        'model': 'dictionary or symbol table as stored; for BIT3 the dictionary entries (1 length byte + bytes each, '
                 'including single bytes added at encode time) and the code-length table (1 byte per entry + 1)',
        'index': 'one 4-byte little-endian offset per record: the end byte offset of the stored record for the baselines, '
                 'the start bit offset for BIT3. The small-block baselines store one such offset per block and one per record',
        'framing': 'bytes inside a stored unit that are container format: zstd frame and block headers; the stored-raw flag '
                   'bitmap of the raw-block method',
        'payload': 'everything else in the stored units; for BIT3 the bit stream, each record ending in an end-of-record code',
    },
    'index_bytes_per_record': 4,
    'index_form': 'one 4-byte offset per record, for every method',
    'why_this_index_form': 'it is the only form the candidate\'s published container and C reader have; the harness serialises '
                           'every baseline in the same form (`bytes.all_in`)',
    'payload_only_bytes': 'the payload part, reported beside the total',
    'reported_not_gated': 'each baseline\'s total with the smallest whole-byte offset width that fits (`all_in_compact_index`)',
    'measured_by': 'fb_measure.measure: `enc.pack(4)` for baselines and candidate alike; the harness checks that the five parts '
                   'sum to the archive length; for the candidate it takes the split between the parts from the adapter, which '
                   'reads it from the archive header',
    'not_counted': 'the decoder program, and for every method the training records',
}

DECISION_RULE = {
    'source': 'PREREGISTRATION.md, section "The gate"; the two numbers are copied from it',
    'decision_workloads': ['w1-short-files', 'w2-message-entries'],
    'spare_workload': 'w3-commit-subjects',
    'passed_if_on_both_decision_workloads': [
        'candidate total bytes are at most 90% of the strongest per-record baseline\'s total bytes',
        'the candidate\'s 95th-percentile lookup time is at most 110% of that baseline\'s',
    ],
    'anything_else': 'not passed; there is no partial pass and no rerun with changed settings',
    'bytes': {'candidate_total_at_most_fraction_of_strongest_per_record_baseline': '0.90'},
    'lookup': {
        'candidate_p95_at_most_fraction_of_that_baseline': '1.10',
        'statistic': 'per_record_mean_p95_ns',
        'statistic_in_words': 'every lookup is timed on its own; for each record the mean of its timings is taken, leaving out '
                              'a timing longer than 8 times that record\'s mean plus 2 microseconds; the 95th percentile '
                              '(nearest rank) of these per-record means is taken across the scored records; the value used '
                              'is the median of that percentile over the timing rounds',
        'why_not_the_percentile_of_single_timings': 'on the scoring machine the timer advances in steps of about 42 ns, which is '
                                                    'more than 10% of a lookup of a few hundred ns; a percentile of single '
                                                    'timings is a multiple of that step. It is reported, not gated',
        'median_reported': 'the median of the per-record means, same treatment',
    },
    'strongest_per_record_baseline': 'among the per-record baselines that reconstruct every record exactly, the one with the '
                                     'fewest total bytes on the scored records; ties go to the earlier one in per_record_order',
    'exact_reconstruction': 'every scored record decoded on its own from the serialised archive in a seeded random order must '
                            'equal the original (harness verification, seed 1 + 17); for the candidate through the Python reader '
                            'and through the C reader. One mismatch disqualifies the method; a disqualified candidate is not passed',
    'candidate_that_cannot_encode_the_scored_records': 'not passed',
    'lookup_timing': {
        'loop': 'fb_native.c `fb_time_lookups`, called through `Native.time_lookups`: one function pointer per method, the '
                'same loop, index sequence and output buffer for every method; the candidate enters it through the harness\'s '
                'native candidate plug-in with the lane\'s C reader (`bit3_decode_one` in ra_codecs_bench.c)',
        'in_memory_and_warm': True,
        'lookups_per_round': 400000,
        'warmup_lookups': 2000,
        'rounds': 9,
        'round_order': 'all methods are timed once per round; round r starts r positions further along the method list',
        'index_sequence_seed': '0x9E3779B97F4A7C15 (the harness constant)',
        'one_machine_one_process': True,
        'quiet_window': {
            'max_load_average_1m_at_start': 3.0,
            'max_load_average_1m_at_end': 3.0,
            'rule': 'the timing pass counts only if the 1-minute load average is at most these values when it starts and when '
                    'it ends. A pass that does not meet this is void, whatever it measured, and the whole scoring command is '
                    'run again unchanged; the first run that meets it counts. The scoring command is run without `nice`, with '
                    'no other measurement running on the machine',
        },
    },
    'spread': {'seed': 20261125, 'resamples': 10000, 'level': '0.95',
               'what': 'interval for candidate total minus strongest-baseline total when the scored sources are resampled '
                       'with replacement; reported, not gated'},
    'reported_separately_not_gated': ['cold open plus first lookup', 'reader heap', 'build time', 'payload-only bytes',
                                      'small-block baselines', 'percentiles of single timings', 'loop mean'],
    'void_run': 'a run that cannot be executed as pinned (a file hash, library version or fitted model differs from this file, or '
                'the candidate\'s C reader cannot be built) is void: it is not a result and does not use up the test set\'s one scoring',
}


def sha256_file(p) -> str:
    return F.sha256_file(p)


def compact_tuning(tuning: dict) -> dict:
    """Every setting tried, as rows [level, dictionary kind, requested size, model bytes, stored validation bytes, objective]."""
    out = {}
    for name, body in tuning['methods'].items():
        rows = [[r['level'], r['dict_kind'], r['dict_bytes_requested'], r['model_bytes'], r['validation_stored_bytes'],
                 r['validation_objective_bytes']] for r in body.get('ranked', [])]
        out[name] = {'settings_in_grid': body.get('settings_in_grid', 0), 'settings_tried': body.get('settings_tried', 0),
                     'settings_not_trainable': body.get('settings_not_trainable', 0),
                     'cover_settings_not_tried': body.get('cover_settings_not_tried', 0),
                     'cover_tried_at_level_and_size': body.get('cover_tried_at_level_and_size'),
                     'chosen': body.get('chosen'), 'validation_all_in': body.get('validation_all_in'),
                     'harness_cross_validation': body.get('harness_cross_validation'),
                     'columns': ['level', 'dict_kind', 'dict_bytes_requested', 'model_bytes', 'validation_stored_bytes',
                                 'validation_objective_bytes'],
                     'ranked': rows}
    return out


def explore_rows(log_path: Path) -> list[dict]:
    rows = []
    for i, line in enumerate(log_path.read_text(encoding='utf-8').splitlines()):
        if line.strip():
            r = json.loads(line)
            r['log_position'] = i
            rows.append(r)
    return rows


def row_ok(r: dict) -> bool:
    v = r.get('verification') or {}
    return (r.get('status') == 'ok' and (v.get('python_reader') or {}).get('ok') is True
            and (v.get('native_reader') or {}).get('ok') is True)


def tried_entry(r: dict) -> dict:
    cfg = r['config']
    e = {'log_position': r['log_position'], 'selection': cfg['selection'], 'arm': cfg['arm'], 'k_max': cfg['k_max'],
         'fit_records': cfg['fit_records'], 'subset_rule': cfg['subset']['rule'],
         'subset_seed': cfg['subset'].get('seed') if cfg['subset']['rule'] == 'sha256-rank' else None,
         'subset_max_records': cfg['subset']['max_records'], 'layout': cfg['layout'], 'status': r['status']}
    if r['status'] != 'ok':
        e['reason'] = r.get('reason')
        return e
    fit, enc, a = r['fit'], r['encode'], r['validation_all_in']
    e.update(k_max_used=fit['k_max_used'], dictionary_entries=fit['dictionary_entries'],
             validation_total_bytes=a['total'], validation_model_bytes=a['model'], validation_index_bytes=a['index'],
             validation_payload_bytes=a['payload'], unseen_single_bytes_added=enc['unseen_single_bytes_added'],
             every_validation_record_exact=row_ok(r), dictionary_sha256=fit['dictionary_sha256'],
             fit_seconds=fit.get('train_seconds'), fitted_from_cache=fit.get('from_cache'))
    if 'lane_predictor' in fit:
        e['lane_predictor'] = fit['lane_predictor']
    return e


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tuning', action='append', required=True, help='workload=path of a tune_baselines.py output')
    ap.add_argument('--explore-log', required=True)
    ap.add_argument('--fidelity')
    ap.add_argument('--notes-json', help='optional JSON object merged into the freeze under "freeze_owner_notes"')
    ap.add_argument('--started-utc', required=True)
    ap.add_argument('--frozen-utc', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--tuning-table-out', required=True)
    args = ap.parse_args()

    tunings = {}
    for item in args.tuning:
        w, _, p = item.partition('=')
        tunings[w] = json.loads(Path(p).read_text(encoding='utf-8'))
    rows = explore_rows(Path(args.explore_log))
    manifest_path = F.LITERALS / 'fresh-short-records-v1' / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))

    def manifest_split(w: str, split: str) -> dict:
        return manifest['workloads'][w]['splits'][split]

    table_doc = {'schema': 'short-record-decision/baseline-tuning-table/v1',
                 'what': 'every baseline setting tried on training and validation records, by workload and method',
                 'objective': next(iter(tunings.values()))['objective'], 'tie_break': next(iter(tunings.values()))['tie_break'],
                 'cover_policy': next(iter(tunings.values()))['cover_policy'],
                 'grid': next(iter(tunings.values()))['grid'], 'workloads': {w: compact_tuning(t) for w, t in tunings.items()}}
    table_path = Path(args.tuning_table_out)
    table_path.write_text(json.dumps(table_doc, separators=(',', ':')) + '\n', encoding='utf-8')

    env0 = next(iter(tunings.values()))['harness']
    workloads, data, tried_all, seeds_tried = {}, {}, {}, {}
    for w in F.WORKLOADS:
        t = tunings[w]
        mine = [r for r in rows if r['workload'] == w]
        for r in mine:
            if r['train_sha256'] != t['inputs']['train']['sha256'] or r['validation_sha256'] != t['inputs']['validation']['sha256']:
                raise SystemExit(f'{w}: a candidate run and the baseline tuning read different files')
        ok = [r for r in mine if row_ok(r)]
        if not ok:
            raise SystemExit(f'{w}: no candidate configuration ran and verified')
        best = min(ok, key=lambda r: (r['validation_all_in']['total'], r['fit']['dictionary_entries'], r['log_position']))
        cfg = dict(best['config'])
        cfg['name'] = 'bits-bit3'
        methods = {}
        for name in PER_RECORD_ORDER + BLOCKS_ORDER:
            b = t['methods'][name]
            ch = b.get('chosen') or {}
            methods[name] = {
                'setting': ({k: ch[k] for k in F.SETTING_KEYS} if all(k in ch for k in F.SETTING_KEYS) else None),
                'dict_bytes_actual': ch.get('dict_bytes_actual', ch.get('exported_table_bytes')),
                'model_sha256': ch.get('model_sha256'),
                'settings_in_grid': b.get('settings_in_grid', 0),
                'settings_tried': b.get('settings_tried', 0),
                'cover_settings_not_tried': b.get('cover_settings_not_tried', 0),
                'validation_all_in': b['validation_all_in'],
            }
            if b.get('harness_cross_validation'):
                hc = b['harness_cross_validation']
                methods[name]['harness_cross_validation_would_pick'] = {
                    **{k: hc['chosen'][k] for k in F.SETTING_KEYS}, 'validation_total_bytes': hc['validation_all_in']['total']}
        workloads[w] = {
            'role': ROLES[w],
            'candidate': {
                'config': cfg,
                'dictionary_sha256': best['fit']['dictionary_sha256'],
                'dictionary_entries': best['fit']['dictionary_entries'],
                'validation_all_in': best['validation_all_in'],
                'validation_unseen_single_bytes_added': best['encode']['unseen_single_bytes_added'],
                'chosen_from_log_position': best['log_position'],
            },
            'baselines': {'per_record_order': PER_RECORD_ORDER, 'blocks_order': BLOCKS_ORDER, 'methods': methods},
        }
        tried_all[w] = [tried_entry(r) for r in mine]
        seeds_tried[w] = sorted({r['config']['subset']['seed'] for r in mine if r['config']['subset']['rule'] == 'sha256-rank'})
        ms_tr, ms_va, ms_te = manifest_split(w, 'train'), manifest_split(w, 'validation'), manifest_split(w, 'test')
        data[w] = {
            'train': {'sha256': t['inputs']['train']['sha256'], 'records': t['inputs']['train']['records'], 'bytes': t['inputs']['train']['bytes'],
                      'sha256_in_manifest': ms_tr['sha256_jsonl']},
            'validation': {'sha256': t['inputs']['validation']['sha256'], 'records': t['inputs']['validation']['records'],
                           'bytes': t['inputs']['validation']['bytes'], 'sha256_in_manifest': ms_va['sha256_jsonl']},
            'test_sha256_from_manifest': ms_te['sha256_test_jsonl'],
            'test_records_from_manifest': ms_te['records'],
        }
        for split in ('train', 'validation'):
            if data[w][split]['sha256_in_manifest'] != data[w][split]['sha256']:
                raise SystemExit(f'{w}: the {split} file read is not the one in the manifest')

    fsst_src = F.N.default_fsst_src()
    try:
        fsst_head = subprocess.run(['git', '-C', str(fsst_src), 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        fsst_head = None
    cc = SCORE.cc_version()
    other = sorted(p.name for p in HERE.iterdir() if p.is_file() and p.name not in ('FREEZE.json', 'FREEZE-NOTES.md', 'dry-run-validation.json'))
    decision_dir = F.LITERALS / 'short-record-decision-v1'
    freeze = {
        'schema': 'short-record-decision/freeze/v1',
        'what_this_is': 'the freeze owner\'s pin of everything that decides the short-record decision test, made on training and '
                        'validation records only, before the test sets are opened',
        'freeze_owner': {
            'who': 'an agent session (model claude-fable-5-2) started for this one task; it wrote neither the codec nor the corpora',
            'read': 'this repository; the training and validation records of the three workloads; the reference FSST sources; '
                    'the exported records of the lane\'s old suites',
            'did_not_read': 'the test records, the test source list, the split salt, the sealed archive, the custodian\'s keys '
                            'or working files, any other session\'s files',
        },
        'times_utc': {'started': args.started_utc, 'frozen': args.frozen_utc, 'clock': 'date -u'},
        'protocol': {'file': 'short-record-decision-v1/PREREGISTRATION.md',
                     'sha256': sha256_file(decision_dir / 'PREREGISTRATION.md')},
        'corpus_manifest': {'file': 'fresh-short-records-v1/manifest.json', 'sha256': sha256_file(manifest_path)},
        'data': data,
        'files': {
            'lane': A.lane_file_hashes(),
            'harness': F.file_hashes(F.HARNESS_FILES),
            'freeze_tools': F.file_hashes(SCORE.FREEZE_TOOL_FILES),
            'fsst_reference': {'commit_named_by_the_custodian': FSST_COMMIT, 'commit_read_from_the_checkout': fsst_head,
                               'files': F.file_hashes(F.FSST_FILES, fsst_src)},
            'other_files_in_this_directory': {name: sha256_file(HERE / name) for name in other},
            'baseline_tuning_table': {'file': 'short-record-decision-v1/' + table_path.name, 'sha256': sha256_file(table_path)},
        },
        'environment': {'zstd_library': env0['zstd_library'], 'zlib_library': env0['zlib_library'],
                        'zstd_linkage': env0['native_helper'].get('zstd_linkage'), 'python': platform.python_version(),
                        'system': platform.system(), 'machine': platform.machine(), 'cc': cc,
                        'enforced_at_scoring': ['zstd_library', 'zlib_library'],
                        'note': 'a different zstd or zlib version can change dictionaries and stored bytes, so scoring stops if '
                                'either differs; every fitted model is also compared with the hash recorded here'},
        'harness_settings': HARNESS_SETTINGS,
        'codec': {
            'item': 1,
            'candidate': 'BITS as published in this repository: the BIT3 container with a static dictionary of byte strings of at '
                         'most 16 bytes, one canonical Huffman code table, an end-of-record code per record and a 4-byte bit '
                         'offset per record',
            'format_version': 'BIT3 (magic bytes "BIT3"), one code table (layout A)',
            'encoder': 'rung2-presearch-v1/run_completed_chain_and_regime_eval.py serialize_and_verify_bit3_archive, with '
                       'codenet-replication-v1/byte_encode.py (minimum-bit parse under fixed code lengths) and '
                       'rung3-archive-search-v1/indexed_archive.py (bit packing)',
            'decoder': 'rung2-short-ra-bench-v1/ra_codecs_bench.c (init_bit3, bit3_decode_one), entered through bits_native_shim.c; '
                       'the Python reader in bits_adapter.py (lane functions) is used for a second verification',
            'adapter': 'short-record-decision-v1/bits_adapter.py:Bit3Candidate; it imports the lane files unmodified (hashes under files.lane)',
            'what_the_archive_takes_from_the_encoded_records': 'single bytes that occur in them and are not dictionary entries: '
                'each is appended to the stored dictionary (2 bytes) with a code length (1 byte), and the code lengths are rebuilt '
                'from the fit-record counts with those bytes at count 1. All of it is inside the archive and counted as model bytes',
            'limits_of_the_lane_code': [
                'engine.c reads at most 2,048 files; the search therefore sees a fixed subset of the training records',
                'the two-table layout needs two known record groups stored as two runs; the workloads have none, so one table is used',
                'the container has one index form (4 bytes per record) and counts records and entries in 16 bits',
                'the C reader has fixed tables for 4,100 symbols, takes no output capacity and reads past the end of the stream; '
                'the shim checks the header and pads a private copy',
            ],
        },
        'training_recipe': {
            'item': 2,
            'steps': [
                'search subset: if the training input has more than subset.max_records records, keep the max_records records whose '
                'index i has the smallest sha256("bits-freeze-subset:<seed>:<i>"), in file order',
                'search: engine.c <arm> s1-whole L=16 K=<k_max> on the search subset, one record per file (equal_budget_eval.run_engine_arm); '
                'the chain must complete (engine_limit_sec is a guard, not a budget)',
                'selection: transfer_vmm.transfer_variational_mm (cells of the lane\'s 2x2) on the fit records with the chain as '
                'candidate strings, or the lane\'s MDL prefix-stop builder (build_and_eval_bit3_pair)',
                'code tables at encode time: minimum-token parse of the fit records, every entry without an occurrence counted once, '
                'canonical Huffman lengths (the lane\'s held-out rule)',
            ],
            'selection_rule': 'per workload, the configuration with the smallest all-in validation bytes among those tried that '
                              'reconstructed every validation record in both readers; ties: fewer dictionary entries, then earlier in the log',
            'dictionary_budget': 'k_max, the number of entries the search may add including single bytes; the selector then keeps a subset',
            'chosen': {w: {'config': workloads[w]['candidate']['config'], 'dictionary_entries': workloads[w]['candidate']['dictionary_entries'],
                           'validation_total_bytes': workloads[w]['candidate']['validation_all_in']['total']} for w in F.WORKLOADS},
            'configurations_tried': tried_all,
        },
        'seed': {
            'item': 3,
            'what_the_seed_does': 'it selects the search subset (see training_recipe.steps). The lane\'s search and selection use no '
                                  'random numbers',
            'rule': 'the seed is part of the configuration and was chosen with it, by validation bytes',
            'chosen': {w: workloads[w]['candidate']['config']['subset'] for w in F.WORKLOADS},
            'seeds_tried': seeds_tried,
            'other_seeds_in_the_scoring_run': {'verification_order': HARNESS_SETTINGS['seed'] + 17,
                                               'timing_index_sequence': '0x9E3779B97F4A7C15',
                                               'spread_resampling': DECISION_RULE['spread']['seed'],
                                               'zstd_dictionary_sample_order': 'the zstd command line\'s fixed shuffle (harness)'},
        },
        'baseline_settings': {
            'item': 4,
            'tuned_by': 'tune_baselines.py: the harness\'s grid `full`, its dictionary trainers and its encoders; every setting fitted '
                        'on the whole training input and measured on the validation records',
            'objective': table_doc['objective'], 'tie_break': table_doc['tie_break'], 'grid': table_doc['grid'],
            'part_of_the_grid_not_searched': table_doc['cover_policy'],
            'harness_default_selection_not_run': 'the harness\'s own 4-fold selection over this grid was not run on these training '
                                                 'inputs: it trains every dictionary five times, including every `cover` dictionary',
            'why_not_the_harness_default_selection': 'the harness\'s default selection cross-validates inside the training input with '
                'folds drawn by record; the splits here are by source, so those folds hold records of the same sources on both sides',
            'per_record_baselines': PER_RECORD_ORDER, 'small_block_baselines_reported_separately': BLOCKS_ORDER,
            'zstd_leanest_framing': 'zstd-raw-block-tuned (no frame; one flag bit per record). zstd-lean-frame-tuned (magicless frame) '
                                    'is pinned and scored too; the strongest is decided by bytes on the scored records',
            'pinned_settings': 'under workloads.<workload>.baselines.methods',
            'every_setting_tried': 'files.baseline_tuning_table',
        },
        'byte_accounting': {'item': 5, **BYTE_ACCOUNTING},
        'decision_rule': {'item': 6, **DECISION_RULE},
        'workloads': workloads,
        'score_command': {
            'per_workload': 'python3 -B score.py run --freeze FREEZE.json --workload <workload> '
                            '--train <custody dir>/release/<workload>/train.jsonl --test <test records>.jsonl --out results-<workload>.json',
            'gate': 'python3 -B score.py gate --freeze FREEZE.json --results results-w1-short-files.json results-w2-message-entries.json '
                    '--out gate.json',
            'environment': 'FAIR_BASELINES_FSST_SRC=<reference FSST checkout>; optionally FAIR_BASELINES_BUILD_DIR=<scratch>',
        },
    }
    if args.fidelity:
        fid = json.loads(Path(args.fidelity).read_text(encoding='utf-8'))
        freeze['adapter_fidelity_check'] = {
            'file': 'short-record-decision-v1/' + Path(args.fidelity).name, 'sha256': sha256_file(args.fidelity),
            'largest_absolute_difference_bytes': fid.get('largest_absolute_difference_bytes'),
            'rows_compared': sum(len(s.get('rows', [])) for s in fid['suites'].values()),
        }
    if args.notes_json:
        freeze['freeze_owner_notes'] = json.loads(Path(args.notes_json).read_text(encoding='utf-8'))
    Path(args.out).write_text(json.dumps(freeze, indent=1) + '\n', encoding='utf-8')
    print(f'wrote {Path(args.out).name} sha256 {sha256_file(args.out)}')
    for w in F.WORKLOADS:
        c = workloads[w]['candidate']
        print(w, 'candidate', {k: c['config'][k] for k in ('selection', 'arm', 'k_max', 'fit_records')}, c['config']['subset'],
              'validation', c['validation_all_in']['total'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
