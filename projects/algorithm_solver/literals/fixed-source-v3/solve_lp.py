#!/usr/bin/env python3
"""The tokenisation LP (Tempus et al., 2026, Eq. 6) and its Det and Bias roundings.

Every string the policy allows gets a selection variable in [0, 1] whose sum is at
most K. A parse is a unit flow over occurrences, each capped by its string's
selection. HiGHS PDLP is a first-order solver. Its value is numerical and is reported
only when the solver says optimal, never as a certificate. A rounded dictionary is kept
when the final point is primal feasible to 1e-3, and is then verified like any other.
Roundings keep the alphabet, then fill to K by LP value, or LP value over length.

    solve_lp.py <v1 private folder> <run folder> <run id> <impl sha> <policy> <corpus> <L> <K> <seconds>
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import highspy
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verify as V


def eligible(docs, limit, policy):
    least, keep_whole, _ = V.POLICIES[policy]
    whole = set(docs)
    ids, strings, starts, lengths, ends = {}, [], [], [], []
    shared = None
    if least == 2:
        owner, shared = {}, set()
        for index, raw in enumerate(docs):
            for at in range(len(raw)):
                for length in range(2, min(limit, len(raw) - at) + 1):
                    piece = raw[at:at + length]
                    mark = owner.get(piece)
                    if mark is None:
                        owner[piece] = index
                    elif mark != index:
                        shared.add(piece)
        del owner
    offset = 0
    for raw in docs:
        for at in range(len(raw)):
            for length in range(1, min(limit, len(raw) - at) + 1):
                piece = raw[at:at + length]
                if length > 1:
                    if not keep_whole and piece in whole:
                        continue
                    if shared is not None and piece not in shared:
                        continue
                code = ids.get(piece)
                if code is None:
                    code = ids[piece] = len(strings)
                    strings.append(piece)
                starts.append(offset + at)
                lengths.append(code)
                ends.append(offset + at + length)
        offset += len(raw) + 1
    return strings, np.array(starts, dtype=np.int32), np.array(lengths, dtype=np.int32), np.array(ends, dtype=np.int32), offset


def build(docs, limit, budget, policy):
    strings, tails, codes, heads, nodes = eligible(docs, limit, policy)
    y, f = len(strings), len(tails)
    source, sink = [], []
    offset = 0
    for raw in docs:
        source.append(offset)
        sink.append(offset + len(raw))
        offset += len(raw) + 1
    demand = np.zeros(nodes)
    demand[source] = 1
    demand[sink] = -1
    # Rows: node balance, then f_e - y_s <= 0, then the budget row.
    edge = np.arange(f, dtype=np.int64)
    row = np.concatenate((tails, heads, nodes + edge, nodes + edge, np.full(y, nodes + f)))
    col = np.concatenate((y + edge, y + edge, y + edge, codes.astype(np.int64), np.arange(y, dtype=np.int64)))
    value = np.concatenate((np.ones(f), -np.ones(f), np.ones(f), -np.ones(f), np.ones(y)))
    order = np.lexsort((row, col))
    row, col, value = row[order], col[order], value[order]
    starts = np.searchsorted(col, np.arange(y + f + 1))
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = y + f, nodes + f + 1
    lp.col_cost_ = np.concatenate((np.zeros(y), np.ones(f)))
    lp.col_lower_, lp.col_upper_ = np.zeros(y + f), np.ones(y + f)
    lp.row_lower_ = np.concatenate((demand, np.full(f, -highspy.kHighsInf), [-highspy.kHighsInf]))
    lp.row_upper_ = np.concatenate((demand, np.zeros(f), [float(budget)]))
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = starts
    lp.a_matrix_.index_ = row.astype(np.int32)
    lp.a_matrix_.value_ = value
    return lp, strings


def rounded(strings, values, budget, biased):
    alphabet = sorted((s for s in strings if len(s) == 1))
    rank = sorted((i for i, s in enumerate(strings) if len(s) > 1),
                  key=lambda i: (-(values[i] / len(strings[i]) if biased else values[i]), strings[i]))
    chosen = alphabet + [strings[i] for i in rank[:max(0, budget - len(alphabet))] if values[i] > 1e-9]
    return chosen


def write_chain(path, entries, header, seconds):
    with open(path, 'w') as out:
        out.write(header + '\n')
        stored = 0
        for index, entry in enumerate(entries):
            stored += 1 + len(entry)
            out.write(f'E {index + 1} {stored} -1 0 {entry.hex()}\n')
        out.write(f'D lp L=0 candidates=0 occurrences=0 stopped=0 seconds={seconds:.1f} enumerate_seconds=0 maxrss_kb=0\n')


def main():
    private, run, run_id, impl, policy, corpus, limit, budget, seconds = (Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4],
                                                                         sys.argv[5], sys.argv[6], int(sys.argv[7]), int(sys.argv[8]), float(sys.argv[9]))
    docs = V.load_corpus(private)[corpus]
    start = time.time()
    lp, strings = build(docs, limit, budget, policy)
    built = time.time() - start
    solver = highspy.Highs()
    solver.setOptionValue('output_flag', False)
    solver.setOptionValue('solver', 'pdlp')
    solver.setOptionValue('pdlp_optimality_tolerance', 1e-4)
    solver.setOptionValue('threads', 4)
    solver.setOptionValue('time_limit', seconds)
    solver.passModel(lp)
    solver.run()
    status = solver.modelStatusToString(solver.getModelStatus())
    info = solver.getInfo()
    report = {'schema': 'gamma.fixed-source-lp.v3', 'policy': policy, 'corpus': corpus, 'L': limit, 'K': budget, 'status': status,
              'columns': lp.num_col_, 'rows': lp.num_row_, 'build_seconds': built, 'solve_seconds': time.time() - start - built,
              'objective': None, 'primal_infeasibility': info.max_primal_infeasibility,
              'dual_infeasibility': info.max_dual_infeasibility, 'label': 'numerical LP value, not an exact certificate'}
    if status == 'Optimal':
        report['objective'] = info.objective_function_value
    report['rounded'] = bool(info.primal_solution_status == 2 or info.max_primal_infeasibility <= 1e-3)
    if report['rounded']:
        values = np.array(solver.getSolution().col_value[:len(strings)])
        manifest = hashlib.sha256(V.MANIFEST.read_bytes()).hexdigest()
        for arm, biased in (('lp-det', False), ('lp-bias', True)):
            entries = rounded(strings, values, budget, biased)
            header = f'H policy={policy} mode={arm} L={limit} K={budget} limit={int(seconds)} manifest={manifest} pool={corpus} cuts=none impl={impl} run={run_id}'
            write_chain(run / 'chains' / policy / f'{corpus}-L{limit}-{arm}-K{budget}.txt', entries, header, time.time() - start)
    (run / 'lp').mkdir(exist_ok=True)
    (run / 'lp' / f'{policy}-{corpus}-L{limit}-K{budget}.json').write_text(json.dumps(report, indent=1) + '\n')
    print({k: report[k] for k in ('policy', 'K', 'status', 'objective', 'solve_seconds')})


if __name__ == '__main__':
    main()
