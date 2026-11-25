# UNFINISHED. Part of a short-record-decision freeze that was paused before FREEZE.json was written.
# Nothing here is pinned. See ../FREEZE-PROGRESS.md for what was run, what was never run, and the next steps.
"""BIT3 candidate adapter for the fair-baselines harness (`short-record-decision-v1`).

The candidate is the lane's own codec as published in this repository. This file writes no
codec logic of its own: it imports the lane's modules unmodified and calls them in the order
the lane's own scripts call them.

    search       ../fixed-source-v3/engine.c, run through equal_budget_eval.run_engine_arm
    selection    run_completed_chain_and_regime_eval.build_and_eval_bit3_pair   (MDL prefix stop)
                 transfer_vmm.transfer_variational_mm                           (the VMM family)
    code tables  byte_encode.segment_corpus_tokens + canonical_huffman_lengths on the fit
                 records, every zero-count entry raised to count 1 (the lane's held-out rule)
    container    run_completed_chain_and_regime_eval.serialize_and_verify_bit3_archive (`BIT3`)
    decoder      indexed_archive.decode_one_doc_from_bit_offset (Python, verification)
                 ../rung2-short-ra-bench-v1/ra_codecs_bench.c through bits_native_shim.c (timing)

Harness plug-in (see ../fair-baselines-v1/fb_candidate.py):

    python3 -B ../fair-baselines-v1/run_fair_baselines.py --train TRAIN --test TEST --out OUT \
        --candidate bits_adapter.py:Bit3Candidate

With `--candidate`, the configuration is read from the environment variable
BITS_ADAPTER_CONFIG (a JSON object, see DEFAULT_CONFIG). `score.py` passes it directly.

What the archive depends on
---------------------------
`train` sees training records only and fixes the dictionary. `encode` adds one thing taken
from the records being encoded, exactly as the lane's scripts do: every single byte that
occurs in those records and is not a dictionary entry is appended to the stored dictionary,
and the code lengths are rebuilt from the fit-record counts with those bytes at count 1.
The appended bytes and all code lengths are inside the archive and are counted as model bytes.
Nothing else is taken from the records being encoded.

Limits of the lane's code that this adapter does not work around
----------------------------------------------------------------
- engine.c reads at most 2,048 files, and the lane's recipe hands it one record per file. A
  larger training input is cut down to `subset.max_records` records by a fixed rule before the
  search. With `fit_records: search-subset` the selection and the code tables use that same
  subset, as in the lane's scripts, where one record set feeds all three steps. With
  `fit_records: all-training` the search still runs on the subset, and the lane's selector
  (`transfer_variational_mm`, which takes a list of candidate strings and a set of records)
  and the code tables are given every training record. The lane's scripts never had to make
  this choice; its MDL prefix-stop builder cannot be split this way.
- The two-table layout needs every record assigned to one of two known groups, stored as two
  contiguous runs. It is used only when the input carries exactly two group labels.
- The container counts entries and records in 16 bits and stores a 4-byte bit offset per
  record; there is no smaller index form. The C reader holds at most 4,100 symbols.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Sequence

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent


def _literals_dir(start: Path) -> Path:
    """The `literals/` directory, found by walking up from this file."""
    for p in (start, *start.parents):
        if (p / 'fair-baselines-v1').is_dir() and (p / 'rung2-short-ra-bench-v1').is_dir():
            return p
    raise RuntimeError('cannot find the literals directory above this file')


LITERALS = _literals_dir(HERE)

# Every lane file this adapter imports (directly or through another lane module) or compiles.
LANE_FILES = (
    'codenet-replication-v1/byte_encode.py',
    'fixed-source-v3/engine.c',
    'rung2-presearch-v1/equal_budget_eval.py',
    'rung2-presearch-v1/raw_predictor.py',
    'rung2-presearch-v1/regime_predictor.py',
    'rung2-presearch-v1/run_completed_chain_and_regime_eval.py',
    'rung2-short-ra-bench-v1/ra_codecs_bench.c',
    'rung3-archive-search-v1/indexed_archive.py',
    'rung3-vmm-subset-v1/transfer_vmm.py',
    'rung3-vmm-subset-v1/vmm_subset_polish.py',
)
_LANE_IMPORT_DIRS = ('codenet-replication-v1', 'rung2-presearch-v1', 'rung3-archive-search-v1', 'rung3-vmm-subset-v1')
for _d in _LANE_IMPORT_DIRS:
    _p = str(LITERALS / _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import byte_encode as BE  # noqa: E402
import equal_budget_eval as EB  # noqa: E402
import indexed_archive as IA  # noqa: E402
import regime_predictor as REG  # noqa: E402
import run_completed_chain_and_regime_eval as RC  # noqa: E402
import transfer_vmm as TV  # noqa: E402

ENGINE_MAX_FILES = 2048      # engine.c: `int cap = 2048` in load(), "too many files" beyond it
C_READER_MAX_SYMBOLS = 4100  # ra_codecs_bench.c: MAX_SYMS, end-of-record symbol included
MAX_CODE_BITS = 32           # ra_codecs_bench.c builds codes in a uint32_t
VMM_CELLS = {                # the lane's 2x2 (evaluate_transfer_vmm_2x2.CELLS_2X2): (revival, shrinkage)
    'base_vmm': (False, 'none'),
    'revival_only_vmm': (True, 'none'),
    'loo_only_vmm': (False, 'loo_doc'),
    'transfer_vmm': (True, 'loo_doc'),
}
ARMS = ('greedy-entry', 'greedy-byte', 'bpe', 'union_bpe_ge')

DEFAULT_CONFIG = {
    # 'A': one code table, one stream, group labels ignored.
    # 'lane-predictor': exactly two groups; layout A or B from the lane's regime_predictor.
    # 'B': exactly two groups, two code tables.
    'layout': 'A',
    # Applied only when the training input has more records than max_records.
    'subset': {'rule': 'sha256-rank', 'max_records': ENGINE_MAX_FILES, 'seed': 1},
    # Records given to the selector and used for the code tables: the records the search saw
    # ('search-subset') or every training record ('all-training'; VMM selections, layout A only).
    'fit_records': 'search-subset',
    'arm': 'greedy-entry',
    'policy': 's1-whole',
    'max_entry_len': 16,
    # dictionary budget handed to the search; 'lane-predictor' takes K_hat from regime_predictor
    'k_max': 1024,
    # wall-clock guard for engine.c. The pinned candidate is the completed chain; a run that
    # the guard stops is an error, never a shorter dictionary.
    'engine_limit_sec': 3600.0,
    'selection': 'transfer_vmm',   # 'mdl_prefix_stop' or one of VMM_CELLS
}


# ---------------------------------------------------------------- provenance

def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lane_file_hashes() -> dict[str, str]:
    return {rel: sha256_file(LITERALS / rel) for rel in LANE_FILES}


def loaded_lane_modules() -> list[str]:
    """Lane source files actually imported into this process (repository-relative to literals/)."""
    out = set()
    for mod in list(sys.modules.values()):
        f = getattr(mod, '__file__', None)
        if not f:
            continue
        p = Path(f).resolve()
        try:
            rel = p.relative_to(LITERALS)
        except ValueError:
            continue
        if rel.parts[0] in ('short-record-decision-v1', 'fair-baselines-v1'):
            continue
        out.add(rel.as_posix())
    return sorted(out)


# Lane files the harness itself may import for its own baselines; not part of the candidate.
HARNESS_SIDE_LANE_FILES = ('rung2-short-ra-bench-v1/fsst255_codec.py',)


def check_lane_imports() -> None:
    extra = [m for m in loaded_lane_modules() if m not in LANE_FILES and m not in HARNESS_SIDE_LANE_FILES]
    if extra:
        raise RuntimeError(f'lane modules imported but not listed in LANE_FILES: {extra}')


def records_digest(records: Sequence[bytes], groups: Sequence[str] | None = None) -> str:
    h = hashlib.sha256()
    for i, r in enumerate(records):
        h.update(struct.pack('<Q', len(r)))
        h.update(r)
        if groups is not None:
            g = str(groups[i]).encode('utf-8')
            h.update(struct.pack('<I', len(g)))
            h.update(g)
    return h.hexdigest()


def entries_digest(entries: Sequence[bytes]) -> str:
    h = hashlib.sha256()
    for e in entries:
        h.update(bytes([len(e)]))
        h.update(e)
    return h.hexdigest()


def build_dir() -> Path:
    env = os.environ.get('FAIR_BASELINES_BUILD_DIR')
    return Path(env) if env else Path(tempfile.gettempdir()) / 'fair-baselines-v1-build'


# ---------------------------------------------------------------- subset rule

def subset_indexes(n: int, rule: dict) -> list[int]:
    """Indexes of the fit records, in original order.

    'sha256-rank': rank every index i by sha256("bits-freeze-subset:<seed>:<i>") and keep the
    max_records smallest. It depends on the seed and on the position of a record in the training
    file, never on its content, and does not rely on any library's random generator.
    'stride': every ceil(n / max_records)-th record, starting at the first.
    """
    m = int(rule['max_records'])
    if m > ENGINE_MAX_FILES:
        raise ValueError(f'engine.c reads at most {ENGINE_MAX_FILES} files')
    if n <= m:
        return list(range(n))
    kind = rule.get('rule', 'sha256-rank')
    if kind == 'sha256-rank':
        seed = int(rule['seed'])
        ranked = sorted(range(n), key=lambda i: hashlib.sha256(f'bits-freeze-subset:{seed}:{i}'.encode('ascii')).digest())
        return sorted(ranked[:m])
    if kind == 'stride':
        step = -(-n // m)
        return list(range(0, n, step))
    raise ValueError(f'unknown subset rule {kind!r}')


# ---------------------------------------------------------------- reader (Python, verification)

class Bit3Reader:
    """Opens a `BIT3` archive from its bytes alone and decodes one record at a time with the
    lane's Python functions (canonical code assignment, decode tree, bit-offset seek)."""

    def __init__(self, archive: bytes):
        if archive[:4] != b'BIT3':
            raise ValueError('not a BIT3 archive')
        n_entries, n_files, n_tables = struct.unpack_from('<HHB', archive, 4)
        if n_tables not in (1, 2):
            raise ValueError('BIT3 archive with an unknown table count')
        pos = 9
        entries = []
        for _ in range(n_entries):
            ln = archive[pos]
            entries.append(archive[pos + 1:pos + 1 + ln])
            pos += 1 + ln
        self.trees = []
        for _ in range(n_tables):
            lengths = {e: archive[pos + k] for k, e in enumerate(entries) if archive[pos + k] > 0}
            lengths[BE.EOF_SYMBOL] = archive[pos + n_entries]
            pos += n_entries + 1
            self.trees.append(BE.build_decode_tree(BE.assign_canonical_codes(lengths)))
        self.index = struct.unpack_from(f'<{n_files}I', archive, pos)
        pos += 4 * n_files
        if n_tables == 2:
            (len1,) = struct.unpack_from('<I', archive, pos)
            pos += 4
            self.streams = (archive[pos:pos + len1], archive[pos + len1:])
        else:
            self.streams = (archive[pos:],)
        self.n_tables = n_tables
        self.count = n_files

    def decode(self, i: int, cap: int = 0) -> bytes:
        word = self.index[i]
        sid, off = ((word >> 31) & 1, word & 0x7FFFFFFF) if self.n_tables == 2 else (0, word)
        return IA.decode_one_doc_from_bit_offset(self.streams[sid], off, self.trees[sid])

    def close(self) -> None:
        pass


def bit3_layout(archive: bytes) -> dict:
    """Byte ranges of a `BIT3` archive, read from the archive itself."""
    n_entries, n_files, n_tables = struct.unpack_from('<HHB', archive, 4)
    pos = 9
    for _ in range(n_entries):
        pos += 1 + archive[pos]
    dict_bytes = pos - 9
    table_bytes = n_tables * (n_entries + 1)
    index_bytes = 4 * n_files
    split_bytes = 4 if n_tables == 2 else 0
    payload = len(archive) - 9 - dict_bytes - table_bytes - index_bytes - split_bytes
    return {'n_entries': n_entries, 'n_records': n_files, 'n_tables': n_tables, 'header_bytes': 9,
            'dictionary_bytes': dict_bytes, 'code_length_table_bytes': table_bytes, 'index_bytes': index_bytes,
            'stream_split_bytes': split_bytes, 'payload_bytes': payload}


# ---------------------------------------------------------------- native decoder build

def _zstd_prefix() -> Path | None:
    cands = []
    env = os.environ.get('FAIR_BASELINES_ZSTD_PREFIX')
    if env:
        cands.append(Path(env))
    cands += [Path('/opt/homebrew'), Path('/usr/local'), Path('/usr')]
    for c in cands:
        if (c / 'include' / 'zstd.h').is_file():
            return c
    return None


def build_native_decoder() -> dict | None:
    """Compile bits_native_shim.c (which includes the lane's ra_codecs_bench.c) outside the
    repository. Returns the harness's native-decoder spec, or None when it cannot be built."""
    shim = HERE / 'bits_native_shim.c'
    lane_c = LITERALS / 'rung2-short-ra-bench-v1' / 'ra_codecs_bench.c'
    prefix = _zstd_prefix()
    if prefix is None:
        return None
    tag = hashlib.sha256(shim.read_bytes() + lane_c.read_bytes() + str(prefix).encode() + sys.platform.encode()).hexdigest()[:16]
    out_dir = build_dir()
    lib = out_dir / f'libbits3-{tag}.{"dylib" if sys.platform == "darwin" else "so"}'
    if not lib.is_file():
        out_dir.mkdir(parents=True, exist_ok=True)
        tmp = out_dir / f'{lib.name}.{os.getpid()}.tmp'
        cmd = [os.environ.get('CC', 'cc'), '-O3', '-fPIC', '-shared', f'-I{prefix / "include"}',
               f'-DBITS_LANE_SOURCE="{lane_c}"', str(shim), f'-L{prefix / "lib"}', '-lzstd', '-lz', '-o', str(tmp)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            sys.stderr.write('BIT3 native decoder could not be built:\n' + proc.stderr[-2000:] + '\n')
            return None
        os.replace(tmp, lib)
    return {'library': str(lib), 'open': 'bits_bit3_open', 'decode': 'bits_bit3_decode', 'close': 'bits_bit3_close',
            'build_tag': tag, 'flags': '-O3 -fPIC -shared, linked with zstd and zlib (the lane\'s file also holds its ZST3 and DFL3 readers)'}


def native_reader_heap_bytes(spec: dict, archive: bytes) -> int | None:
    try:
        lib = ctypes.CDLL(spec['library'])
        lib.bits_bit3_open.restype = ctypes.c_void_p
        lib.bits_bit3_open.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        lib.bits_bit3_reader_heap_bytes.restype = ctypes.c_size_t
        lib.bits_bit3_reader_heap_bytes.argtypes = [ctypes.c_void_p]
        lib.bits_bit3_close.argtypes = [ctypes.c_void_p]
        h = lib.bits_bit3_open(archive, len(archive))
        if not h:
            return None
        n = lib.bits_bit3_reader_heap_bytes(h)
        lib.bits_bit3_close(h)
        return int(n)
    except Exception:
        return None


# ---------------------------------------------------------------- the candidate

class Bit3Candidate:
    name = 'bits-bit3'
    label = 'BITS: the lane\'s BIT3 container, dictionary and code tables from its own training code'

    def __init__(self, config: dict | None = None):
        if config is None:
            raw = os.environ.get('BITS_ADAPTER_CONFIG')
            config = json.loads(raw) if raw else {}
        cfg = json.loads(json.dumps(DEFAULT_CONFIG))
        for k, v in config.items():
            if k == 'subset':
                cfg['subset'].update(v)
            else:
                cfg[k] = v
        unknown = set(cfg) - set(DEFAULT_CONFIG) - {'name'}
        if unknown:
            raise ValueError(f'unknown configuration keys: {sorted(unknown)}')
        if cfg['layout'] not in ('A', 'B', 'lane-predictor'):
            raise ValueError('layout must be A, B or lane-predictor')
        if cfg['arm'] not in ARMS:
            raise ValueError(f'arm must be one of {ARMS}')
        if cfg['selection'] != 'mdl_prefix_stop' and cfg['selection'] not in VMM_CELLS:
            raise ValueError('selection must be mdl_prefix_stop or one of ' + ', '.join(VMM_CELLS))
        if cfg['selection'] == 'mdl_prefix_stop' and cfg['arm'] != 'greedy-entry':
            raise ValueError('the lane\'s MDL prefix-stop builder (build_and_eval_bit3_pair) searches with greedy-entry only')
        if cfg['fit_records'] not in ('search-subset', 'all-training'):
            raise ValueError('fit_records must be search-subset or all-training')
        if cfg['fit_records'] == 'all-training' and (cfg['selection'] == 'mdl_prefix_stop' or cfg['layout'] != 'A'):
            raise ValueError('fit_records all-training is available for the VMM selections in layout A only: the lane\'s '
                             'MDL prefix-stop builder searches and selects on one record set')
        if 'name' in cfg:
            self.name = str(cfg.pop('name'))
        self.cfg = cfg
        self.entries: list[bytes] | None = None
        self.fit_1: list[bytes] = []   # records the selector and the code tables see
        self.fit_2: list[bytes] = []
        self.search_docs: list[bytes] = []   # records the engine sees (at most ENGINE_MAX_FILES)
        self.n_tables = 1
        self.group_labels: list[str] | None = None
        self.train_report: dict = {}
        self.last_encode_report: dict = {}
        self.last_archive: bytes | None = None
        self._engine: Path | None = None

    # ---- helpers

    def _engine_bin(self) -> Path:
        if self._engine is None:
            src = LITERALS / 'fixed-source-v3' / 'engine.c'
            self._engine = EB.compile_engine(build_dir() / f'bits-engine-{sha256_file(src)[:16]}')
        return self._engine

    def _split(self, records: Sequence[bytes], groups: Sequence[str] | None, *, fitting: bool) -> tuple[list[bytes], list[bytes]]:
        """Two contiguous groups in a fixed order, or everything in the first stream."""
        records = list(records)
        if self.cfg['layout'] == 'A':
            return records, []
        if groups is None:
            raise ValueError('this layout needs two group labels on the records')
        runs: list[str] = []
        for g in groups:
            if not runs or runs[-1] != g:
                runs.append(g)
        if len(runs) != 2 or len(set(runs)) != 2:
            raise ValueError('this layout needs exactly two groups, each stored as one contiguous run')
        if fitting:
            self.group_labels = runs
        elif runs != self.group_labels:
            raise ValueError('the records to encode do not carry the two training groups in the training order')
        return ([r for r, g in zip(records, groups) if g == runs[0]], [r for r, g in zip(records, groups) if g == runs[1]])

    def _chain(self, docs: Sequence[bytes], arm: str, k_max: int) -> tuple[list[bytes], dict]:
        """One completed search chain from the lane's engine, called as the lane's scripts call it."""
        limit = float(self.cfg['engine_limit_sec'])
        work = build_dir()
        work.mkdir(parents=True, exist_ok=True)
        cache = None
        if os.environ.get('BITS_ADAPTER_CACHE_DIR'):   # exploration only; see _cache_path
            key = hashlib.sha256(json.dumps({
                'docs': records_digest(docs), 'arm': arm, 'policy': self.cfg['policy'], 'L': int(self.cfg['max_entry_len']),
                'k': int(k_max), 'engine': sha256_file(LITERALS / 'fixed-source-v3' / 'engine.c'),
            }, sort_keys=True).encode('utf-8')).hexdigest()
            cache = Path(os.environ['BITS_ADAPTER_CACHE_DIR']) / f'bit3-chain-{key[:32]}.json'
            if cache.is_file():
                saved = json.loads(cache.read_text(encoding='utf-8'))
                return [bytes.fromhex(x) for x in saved['chain_hex']], {**saved['info'], 'from_cache': True}
        with tempfile.TemporaryDirectory(prefix='bits-adapter-', dir=str(work)) as tmp:
            wdir = Path(tmp)
            lf = EB.write_corpus_list(list(docs), wdir, 'both', list(range(len(docs))))
            cp = wdir / f'{arm}.txt'
            t0 = time.perf_counter()
            EB.run_engine_arm(self._engine_bin(), arm=arm, policy=self.cfg['policy'], max_entry_len=int(self.cfg['max_entry_len']),
                              k_max=int(k_max), limit_sec=limit, list_file=lf, out_chain=cp, run_tag='freeze')
            sec = time.perf_counter() - t0
            stopped = None
            for line in cp.read_text(encoding='utf-8').splitlines():
                if line.startswith('D '):
                    for tok in line.split():
                        if tok.startswith('stopped='):
                            stopped = int(tok.split('=', 1)[1])
            chain = [e for _, _, e in EB.read_chain_entries(cp)]
        if stopped != 0:
            raise RuntimeError(f'engine.c did not complete the {arm} search within {limit:.0f} s (stopped={stopped}); '
                               'the pinned candidate is defined by the completed chain')
        info = {'arm': arm, 'k_max': int(k_max), 'chain_entries': len(chain), 'engine_seconds': round(sec, 2), 'stopped': stopped}
        if cache is not None:
            cache.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = cache.with_suffix(f'.{os.getpid()}.tmp')
            tmp_path.write_text(json.dumps({'chain_hex': [e.hex() for e in chain], 'info': info}), encoding='utf-8')
            os.replace(tmp_path, cache)
        return chain, info

    def _frozen_lengths(self, entries: Sequence[bytes]) -> tuple[dict, ...]:
        """The lane's held-out code tables (run_completed_chain_and_regime_eval.build_and_eval_bit3_pair,
        evaluate_vmm_rung3.serialize_in_and_heldout_bit3_with_c_speed): minimum-token parse of the
        fit records, every entry without an occurrence counted once."""
        root = BE.build_trie(entries)
        groups = (self.fit_1 + self.fit_2,) if self.n_tables == 1 else (self.fit_1, self.fit_2)
        tables = []
        for docs in groups:
            _, counts, _ = BE.segment_corpus_tokens(docs, root)
            if counts is None:
                raise RuntimeError('the dictionary cannot spell the fit records')
            smoothed = Counter(counts)
            for e in entries:
                if smoothed[e] == 0:
                    smoothed[e] = 1
            tables.append(BE.canonical_huffman_lengths(smoothed))
        return tuple(tables)

    # ---- plug-in interface

    def train(self, train_records, train_groups):
        cfg = self.cfg
        t0 = time.perf_counter()
        check_lane_imports()
        all_1, all_2 = self._split(train_records, train_groups, fitting=True)
        n_in = len(all_1) + len(all_2)
        report: dict = {'recipe': dict(cfg), 'training_records_given': n_in}
        if cfg['layout'] == 'A':
            idx = subset_indexes(len(all_1), cfg['subset'])
            self.search_docs = [all_1[i] for i in idx]
            self.fit_1 = list(all_1) if cfg['fit_records'] == 'all-training' else list(self.search_docs)
            self.fit_2 = []
            report['search_subset'] = {
                'records': len(idx), 'bytes': sum(len(r) for r in self.search_docs),
                'applied': len(idx) < len(all_1),
                'index_sha256': hashlib.sha256(struct.pack(f'<{len(idx)}I', *idx)).hexdigest(),
            }
        else:
            if n_in > ENGINE_MAX_FILES:
                raise ValueError(f'the grouped layouts are run without a subset; engine.c reads at most {ENGINE_MAX_FILES} files')
            self.fit_1, self.fit_2 = all_1, all_2
            self.search_docs = all_1 + all_2
            report['search_subset'] = {'records': n_in, 'bytes': sum(len(r) for r in all_1 + all_2), 'applied': False}
        fit_all = self.fit_1 + self.fit_2
        report['fit_records'] = {'records': len(fit_all), 'bytes': sum(len(r) for r in fit_all)}

        layout, k_max = cfg['layout'], cfg['k_max']
        if layout == 'lane-predictor' or k_max == 'lane-predictor':
            # the lane's rule reads the records the search will see
            pred_docs = (self.search_docs, []) if cfg['layout'] == 'A' else (self.fit_1, self.fit_2)
            pred = REG.predict_codec_and_layout_regime(*pred_docs)
            report['lane_predictor'] = {'layout_hat': pred['layout_hat'], 'K_hat': pred['K_hat'],
                                        'held_out_codec_hat': pred['held_out_codec_hat'],
                                        'regime_rule_version': pred['regime_rule_version'],
                                        'layout_rule_version': pred['layout_rule_version']}
            if layout == 'lane-predictor':
                layout = 'A' if pred['layout_hat'] == 'A' else 'B'   # as run_ra_pareto_bench.evaluate_suite
            if k_max == 'lane-predictor':
                k_max = int(pred['K_hat'])
        k_max = int(k_max)
        self.n_tables = 1 if layout == 'A' else 2
        report.update(layout_used=layout, n_tables=self.n_tables, k_max_used=k_max)

        cache = self._cache_path(train_records, train_groups)
        if cache is not None and cache.is_file():
            saved = json.loads(cache.read_text(encoding='utf-8'))
            self.entries = [bytes.fromhex(x) for x in saved['entries_hex']]
            report.update(saved['report_tail'])
            report['from_cache'] = True
        else:
            tail: dict = {}
            if cfg['selection'] == 'mdl_prefix_stop':
                # The lane's builder also packs a held-out archive and returns only sizes. It is given
                # one fit record per stream as a stand-in for held-out data and that output is dropped;
                # the dictionary it selects depends on the fit records alone. The chain is then run
                # again and cut at the selected size, as run_ra_pareto_bench.evaluate_suite does.
                stand_1 = [self.fit_1[0]]
                stand_2 = [self.fit_2[0]] if self.fit_2 else []
                meta = RC.build_and_eval_bit3_pair(self._engine_bin(), self.fit_1, self.fit_2, stand_1, stand_2,
                                                   layout=layout, k_cap=k_max, limit_sec=float(cfg['engine_limit_sec']))
                chain, info = self._chain(self.search_docs, 'greedy-entry', k_max)
                self.entries = chain[:int(meta['selected_entries'])]
                tail.update(search=[info], selected_entries=int(meta['selected_entries']),
                            fit_archive_bytes_reported_by_lane_builder=int(meta['in_sample_bytes']))
            else:
                revival, shrinkage = VMM_CELLS[cfg['selection']]
                if cfg['arm'] == 'union_bpe_ge':
                    c_bpe, i_bpe = self._chain(self.search_docs, 'bpe', k_max)
                    c_ge, i_ge = self._chain(self.search_docs, 'greedy-entry', k_max)
                    seed_entries = list(dict.fromkeys(c_bpe + c_ge))   # as evaluate_transfer_vmm_2x2
                    infos = [i_bpe, i_ge]
                else:
                    seed_entries, info = self._chain(self.search_docs, cfg['arm'], k_max)
                    infos = [info]
                tv = TV.transfer_variational_mm(self.fit_1, self.fit_2, seed_entries, n_tables=self.n_tables,
                                                revival=revival, shrinkage=shrinkage)
                self.entries = list(tv['entries'])
                tail.update(search=infos, seed_entries=len(seed_entries), revival=revival, shrinkage=shrinkage,
                            certified_nash=bool(tv['is_certified_nash_fixed_point']),
                            revived_substrings_used=int(tv.get('revived_substrings_used', 0)),
                            fit_archive_bytes_without_index=int(tv['total_archive_bytes']))
            report.update(tail)
            report['from_cache'] = False
            if cache is not None:
                cache.parent.mkdir(parents=True, exist_ok=True)
                tmp = cache.with_suffix(f'.{os.getpid()}.tmp')
                tmp.write_text(json.dumps({'entries_hex': [e.hex() for e in self.entries], 'report_tail': tail}), encoding='utf-8')
                os.replace(tmp, cache)

        if len(set(self.entries)) != len(self.entries):
            raise RuntimeError('duplicate dictionary entries')
        report.update(
            dictionary_entries=len(self.entries),
            dictionary_single_byte_entries=sum(1 for e in self.entries if len(e) == 1),
            dictionary_stored_bytes=sum(1 + len(e) for e in self.entries),
            dictionary_sha256=entries_digest(self.entries),
            train_seconds=round(time.perf_counter() - t0, 2),
        )
        self.train_report = report
        return report

    def _cache_path(self, records, groups) -> Path | None:
        """Opt-in cache of trained dictionaries, used while exploring configurations. score.py removes
        the variable, so a scoring run always trains from the training records."""
        root = os.environ.get('BITS_ADAPTER_CACHE_DIR')
        if not root:
            return None
        key = hashlib.sha256(json.dumps({
            'cfg': {k: v for k, v in self.cfg.items()}, 'records': records_digest(records, groups),
            'lane': lane_file_hashes(),
        }, sort_keys=True).encode('utf-8')).hexdigest()
        return Path(root) / f'bit3-model-{key[:32]}.json'

    def encode(self, records, groups):
        if self.entries is None:
            raise RuntimeError('train() has not been called')
        records = list(records)
        docs_1, docs_2 = self._split(records, groups, fitting=False)
        if len(records) > 0xFFFF:
            raise ValueError('the BIT3 container counts records in 16 bits')
        # Single bytes of these records that the dictionary lacks: appended to the stored dictionary.
        present = set(self.entries)
        unseen = sorted({bytes([b]) for d in records for b in d if bytes([b]) not in present})
        entries = list(self.entries) + unseen
        if len(entries) + 1 > C_READER_MAX_SYMBOLS:
            raise ValueError(f'{len(entries)} dictionary entries exceed the C reader\'s {C_READER_MAX_SYMBOLS}-symbol tables')
        frozen = self._frozen_lengths(entries)
        longest = max(max(t.values()) for t in frozen)
        if longest > MAX_CODE_BITS:
            raise ValueError(f'a {longest}-bit code exceeds what the C reader builds')
        archive, _ = RC.serialize_and_verify_bit3_archive(entries, docs_1, docs_2, n_tables=self.n_tables, frozen_lengths=frozen)
        lay = bit3_layout(archive)
        stream_bits_limit = (1 << 31) if self.n_tables == 2 else (1 << 32)
        if lay['payload_bytes'] * 8 >= stream_bits_limit:
            raise ValueError('the bit stream is too long for the 4-byte bit offsets')
        accounting = {
            'header': lay['header_bytes'],
            'model': lay['dictionary_bytes'] + lay['code_length_table_bytes'],
            'index': lay['index_bytes'],
            'framing': lay['stream_split_bytes'],
            'payload': lay['payload_bytes'],
        }
        unseen_occ = {u: sum(d.count(u) for d in records) for u in unseen}
        table_for_unseen = frozen[0]
        self.last_encode_report = {
            'layout': lay,
            'entries_from_training': len(self.entries),
            'unseen_single_bytes_added': len(unseen),
            'unseen_single_byte_occurrences': sum(unseen_occ.values()),
            'records_containing_an_unseen_byte': sum(1 for d in records if any(u in d for u in unseen)),
            'model_bytes_for_unseen_single_bytes': len(unseen) * (2 + self.n_tables),
            'payload_bits_on_unseen_single_byte_codes': (sum(unseen_occ[u] * table_for_unseen[u] for u in unseen)
                                                       if self.n_tables == 1 else None),
            'longest_code_bits': longest,
            'archive_sha256': hashlib.sha256(archive).hexdigest(),
        }
        self.last_archive = archive
        return {'archive': archive, 'accounting': accounting, 'like_for_like_bytes': len(archive)}

    def open(self, archive):
        return Bit3Reader(bytes(archive))

    def native_decoder(self):
        spec = build_native_decoder()
        if spec is None:
            return None
        return {k: spec[k] for k in ('library', 'open', 'decode', 'close')}
