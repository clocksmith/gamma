#!/usr/bin/env python3
"""Write RESULTS.md and out/rule-outcomes.json from the scorer's files.

    python3 make_results.py [--out DIR]

No measured number is typed by hand. The six preregistered rules are evaluated once, in
evaluate_rules(), and written to out/rule-outcomes.json; RESULTS.md and the paper read their
outcomes from there. Every sentence that states an outcome is either built from the data or
guarded by need(), which stops the script instead of writing a sentence the data no longer
supports. --out writes both files to another directory and leaves this folder untouched
(replay.py uses it to check that the committed files regenerate).
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SETS = ('train', 'dev', 'fresh', 'project')
SET_LABEL = {'train': 'training', 'dev': 'development', 'fresh': 'new problems', 'project': 'project'}
ARMS = ('chars', 'bpe', 'freq', 'length', 'token', 'bytes')
LABEL = {'chars': 'single bytes only', 'bpe': 'BPE', 'freq': 'raw frequency', 'length': 'length-weighted (control)',
         'token': 'token gain', 'bytes': 'archive bytes'}
CAPS = (256, 4096)
ZD = 'zstd-19 per file, trained 8 KiB dictionary'
ZS = 'zstd-19 one stream, no dictionary'
THRESHOLD = 1.0  # percent; PREREGISTRATION.md, "Decision rules": a difference under 1.0% is no difference
CONTRACTS = (('complete', 'sequential, everything counted'), ('random_access_complete', 'random access, index counted'),
             ('dictionary_already_held', 'dictionary already held by the reader'))
SMALL = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten')


def n(x):
    return f'{x:,}'


def pct(a, b):
    return f'{100.0 * (a - b) / b:+.1f}%'


def need(cond, message):
    if not cond:
        raise SystemExit(f'make_results.py: nothing written. {message}')


def evaluate_rules(res):
    """The six rules of PREREGISTRATION.md, "Hypotheses", as written there. `fresh` decides; the
    comparisons use exact counts, not rounded percentages."""
    def H(s, name):
        return res[s]['headers'][name]

    def paired(s, cap, a, b):
        return next(x for x in res[s]['paired'] if x['cap'] == cap and x['a'] == a and x['b'] == b)

    def smaller_by_threshold(a, b):
        return a <= (1.0 - THRESHOLD / 100.0) * b

    rules = {}
    by_cap = {}
    for cap in CAPS:
        t = paired('fresh', cap, 'token', 'bpe')['tokens']
        a, b = H('fresh', f'token-K{cap}')['min_tokens'], H('fresh', f'bpe-K{cap}')['min_tokens']
        by_cap[str(cap)] = {
            'token_gain_tokens': a, 'bpe_tokens': b, 'percent': round(100.0 * (a - b) / b, 4),
            'problems_lower': t['units_a_lower'], 'problems_higher': t['units_a_higher'], 'problems_tied': t['units_tied'],
            'sign_test_two_sided_p': t['sign_test_two_sided_p'],
            'holds': smaller_by_threshold(a, b) and t['units_a_lower'] > t['units_a_higher'] and t['sign_test_two_sided_p'] < 0.05,
        }
    rules['T'] = {'statement': 'Token savings transfer', 'holds': all(c['holds'] for c in by_cap.values()), 'by_cap': by_cap}

    tok, byt = H('fresh', 'token-K4096')['bytes'], H('fresh', 'bytes-K4096')['bytes']
    rules['B'] = {
        'statement': 'The byte objective wins archives',
        'holds': smaller_by_threshold(byt['complete'], tok['complete']),
        'bytes_archive': byt['complete'], 'token_archive': tok['complete'],
        'bytes_header': byt['header'], 'token_header': tok['header'],
        'same_dictionary_at_256': H('fresh', 'bytes-K256')['archive_sha256'] == H('fresh', 'token-K256')['archive_sha256'],
    }

    by_cap = {}
    for cap in CAPS:
        ln, tk = H('fresh', f'length-K{cap}'), H('fresh', f'token-K{cap}')
        by_cap[str(cap)] = {'more_tokens': ln['min_tokens'] > tk['min_tokens'],
                            'larger_archive': ln['bytes']['complete'] > tk['bytes']['complete']}
    rules['C'] = {'statement': 'The negative control behaves as one',
                  'holds': all(c['more_tokens'] and c['larger_archive'] for c in by_cap.values()), 'by_cap': by_cap}

    cls = H('fresh', 'token-K4096')['by_train_reuse_class']
    share = {k: cls[k]['pays_rent'] / cls[k]['entries'] for k in ('1', '4+')}
    rules['R'] = {'statement': 'Reuse predicts rent', 'holds': share['4+'] > share['1'],
                  'share_paying_used_by_four_or_more': round(share['4+'], 6), 'share_paying_used_by_one': round(share['1'], 6)}

    xp = H('fresh', 'token-K4096.xp')['bytes']
    rules['X'] = {'statement': 'Single-problem fragments cost bytes', 'holds': smaller_by_threshold(xp['complete'], tok['complete']),
                  'archive_without_them': xp['complete'], 'token_archive': tok['complete']}

    by_contract = {}
    for key, label in CONTRACTS:
        row = {'contract': label}
        for s in ('fresh', 'project'):
            best, arm = min((H(s, f'{a}-K{c}')['bytes'][key], f'{a}-K{c}') for a in ARMS[1:] for c in CAPS)
            z = res[s]['zstd']['rows'][ZD][key]
            row[s] = {'best_bits': best, 'best_bits_dictionary': arm, 'zstd_trained_dictionary': z, 'holds': smaller_by_threshold(best, z)}
        row['holds'] = row['fresh']['holds'] and row['project']['holds']
        by_contract[key] = row
    rules['Z'] = {'statement': 'BITS beats trained zstd', 'holds': by_contract['complete']['holds'],
                  'decided_on': 'complete archives; the other contracts are reported', 'by_contract': by_contract}
    return rules


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', help='write RESULTS.md and rule-outcomes.json here instead of into this folder')
    args = ap.parse_args()
    raw = {s: (HERE / 'out' / f'results-{s}.json').read_bytes() for s in SETS}
    res = {s: json.loads(raw[s]) for s in SETS}
    fresh = json.loads((HERE / 'sets' / 'fresh.json').read_text())
    project = json.loads((HERE / 'sets' / 'project.json').read_text())
    decode = {s: json.loads((HERE / 'out' / f'decode-{s}.json').read_text()) for s in SETS}

    # "Decoded byte for byte" is a claim about the decoder's verdicts, not about how many reports exist.
    for s in SETS:
        d = decode[s]
        need(d['all_ok'] is True and not d['failures'], f'the independent decoder reports a failure on {s}: {d["failures"][:3]}')
        need(d['compared_with_sha256'] == hashlib.sha256(raw[s]).hexdigest(), f'decode-{s}.json was made against a different results-{s}.json')
        need(sorted(d['headers']) == sorted(res[s]['headers']) and d['archives'] == len(d['headers']), f'{s}: decoder and scorer list different archives')
        need(all(h['ok'] and h['all_files_equal'] and h['files_differing_from_source'] == 0 for h in d['headers'].values()),
             f'{s}: an archive did not decode to its source files')

    def H(s, arm, cap, v=''):
        return res[s]['headers'][f'{arm}-K{cap}{v}']

    def paired(s, cap, a, b):
        return next(x for x in res[s]['paired'] if x['cap'] == cap and x['a'] == a and x['b'] == b)

    rules = evaluate_rules(res)

    out = []
    w = out.append
    w('# Results: which selection objective survives on unseen code (`objective-holdout-v1`)')
    w('')
    w('Generated by `make_results.py` from `out/results-*.json`. Rules and metrics: [`PREREGISTRATION.md`](PREREGISTRATION.md),')
    w('committed at `54f4ca1f9` before training. Dictionaries, code tables and commands frozen at `9d7d54b9e` before any test')
    w('file was fetched. One deviation, recorded before any result was read: [`DEVIATIONS.md`](DEVIATIONS.md). The scorer\'s')
    w('account of what it ran: [`SCORER-LOG.md`](SCORER-LOG.md). The outcome of each rule is also in')
    w('[`out/rule-outcomes.json`](out/rule-outcomes.json), which this script writes and the paper reads.')
    w('')
    w('## Outcome of each rule')
    w('')
    t256, t4096 = rules['T']['by_cap']['256'], rules['T']['by_cap']['4096']
    tok, byt = H('fresh', 'token', 4096), H('fresh', 'bytes', 4096)
    cls = tok['by_train_reuse_class']
    xp = H('fresh', 'token', 4096, '.xp')

    def best(s):
        return min((H(s, a, c)['bytes']['complete'], f'{LABEL[a]} at {n(c)}') for a in ARMS[1:] for c in CAPS)

    hold = lambda b: '**holds**' if b else '**fails**'
    w('| Rule | Outcome | Measured on the new problems |')
    w('| --- | --- | --- |')
    w(f'| **T** token savings transfer | {hold(rules["T"]["holds"])} | At 256, token gain uses {t256["percent"]:+.1f}% tokens against BPE and is '
      f'lower on {t256["problems_lower"]} of {res["fresh"]["units"]} problems. At 4,096 it uses {t4096["percent"]:+.1f}% and is '
      f'lower on {t4096["problems_lower"]}, higher on {t4096["problems_higher"]}. In training it was '
      f'{pct(H("train", "token", 4096)["min_tokens"], H("train", "bpe", 4096)["min_tokens"])} |')
    same256 = 'the two rules chose the same dictionary' if rules['B']['same_dictionary_at_256'] else 'the two rules chose different dictionaries'
    w(f'| **B** the byte objective wins archives | {hold(rules["B"]["holds"])} | At 4,096 the archive-bytes archive is {n(byt["bytes"]["complete"])} B '
      f'against {n(tok["bytes"]["complete"])} B for token gain ({pct(byt["bytes"]["complete"], tok["bytes"]["complete"])}). '
      f'At 256 {same256} |')
    control = ('Length-weighted frequency is worse than token gain on tokens and on bytes at both caps' if rules['C']['holds']
               else 'Length-weighted frequency is not worse than token gain on every measure; see the tables below')
    w(f'| **C** the negative control behaves as one | {hold(rules["C"]["holds"])} | {control} |')
    w(f'| **R** reuse predicts rent | {hold(rules["R"]["holds"])} | Of token-gain fragments used by four or more training problems, '
      f'{cls["4+"]["pays_rent"]} of {n(cls["4+"]["entries"])} pay rent; of those used by one, {cls["1"]["pays_rent"]} of {n(cls["1"]["entries"])} |')
    w(f'| **X** single-problem fragments cost bytes | {hold(rules["X"]["holds"])} | Dropping them changes the token-gain archive by '
      f'{pct(xp["bytes"]["complete"], tok["bytes"]["complete"])} and its tokens by {pct(xp["min_tokens"], tok["min_tokens"])} |')
    zf, zp = res['fresh']['zstd']['rows'][ZD]['complete'], res['project']['zstd']['rows'][ZD]['complete']
    zc = rules['Z']['by_contract']
    others = [zc[k] for k, _ in CONTRACTS[1:]]
    if not any(c['holds'] for c in others):
        other_contracts = 'It fails under the other two access contracts as well'
    else:
        other_contracts = 'Under the other access contracts: ' + '; '.join(f'{c["contract"]}, {"holds" if c["holds"] else "fails"}' for c in others)
    w(f'| **Z** BITS beats trained zstd | {hold(rules["Z"]["holds"])} | Best BITS archive {n(best("fresh")[0])} B ({best("fresh")[1]}) against {n(zf)} B '
      f'({pct(best("fresh")[0], zf)}); on the project {n(best("project")[0])} B ({best("project")[1]}) against {n(zp)} B '
      f'({pct(best("project")[0], zp)}). {other_contracts} |')
    w('')

    def coded(s, arm):
        b = H(s, arm, 4096)['bytes']
        return b['complete'] - b['header']

    word = lambda b: 'holds' if b else 'fails'
    gap_complete = tok['bytes']['complete'] - byt['bytes']['complete']
    gap_header = tok['bytes']['header'] - byt['bytes']['header']
    need(abs(coded('fresh', 'bytes') - coded('fresh', 'token')) <= 0.001 * coded('fresh', 'token')
         and abs(gap_complete - gap_header) <= 0.001 * abs(gap_complete),
         'the reading "same coded bytes, the difference is the stored dictionary" no longer matches the data; rewrite that paragraph')
    need(t256['holds'] and all(H('project', 'token', c)['min_tokens'] > H('project', 'bpe', c)['min_tokens'] for c in CAPS),
         'the sentence about the 256 cap and the project no longer matches the data; rewrite it')
    w(f'By the preregistered reading T {word(rules["T"]["holds"])} and B {word(rules["B"]["holds"])}. Two reviews after scoring showed what B does and does not mean:')
    w('the byte-selected and token-gain dictionaries code the unseen files in the same number of bytes, and the whole')
    w('difference between their archives is the stored dictionary. See "Where the archive bytes are" below and the')
    w('post-scoring measurements in `out/posthoc-exploration.json`. The token advantage carries to new problems at the')
    w('256 cap and not to the project at either cap.')
    w('')
    w('## Where the archive bytes are (4,096 cap)')
    w('')
    w('| Rule | Fragments | Header | Coded files, training | Coded files, new problems | Complete, new problems |')
    w('| --- | ---: | ---: | ---: | ---: | ---: |')
    for arm in ('bpe', 'token', 'bytes'):
        fr = H('fresh', arm, 4096)['bytes']
        w(f'| {LABEL[arm]} | {n(H("fresh", arm, 4096)["multi_byte_entries"])} | {n(fr["header"])} | {n(coded("train", arm))} | '
          f'{n(coded("fresh", arm))} | {n(fr["complete"])} |')
    w('')
    w('The header is fixed, so which archive is smallest depends on how much text shares it. These figures are for a')
    w(f'test set of {n(res["fresh"]["source_bytes"])} bytes; the training set has {n(res["train"]["source_bytes"])}.')
    w('')
    w('## Test sets')
    w('')
    sel = fresh['selection']
    need(sel['ranks_0_399_reproduce_frozen_manifest'] is True, 'the selection rule did not reproduce the earlier manifest')
    tried, order = project['selection']['tried'], project['selection']['candidate_order']
    need(len(tried) == 1 and tried[0]['repository'] == order[0], 'more than the first candidate repository was opened')
    need(len({f['lang'] for f in project['files']}) == 1, 'the project files are not all one language')
    w(f'- **New problems:** {res["fresh"]["units"]} CodeNet problems, {res["fresh"]["files"]} files, {n(res["fresh"]["source_bytes"])} bytes, '
      f'ranks {sel["first_rank"]} to {sel["last_rank"]}. The rule reproduced all {res["train"]["files"] + res["dev"]["files"]} earlier files exactly before drawing new ones. '
      f'Skipped: {len(sel["skipped"])} ({"; ".join(s["p_id"] + ", " + s["reason"] for s in sel["skipped"])}).')
    w(f'- **Project:** {project["source"]}. {project["selection"]["eligible_files"]} eligible files, {len(project["files"])} kept, '
      f'{n(res["project"]["source_bytes"])} bytes, all {project["files"][0]["lang"]}. First of {len(order)} in the hashed candidate order; no other repository was opened.')
    w(f'- **Decode:** the scorer\'s decoder, written from `FORMAT.md` alone, rebuilt every file from every archive: '
      f'{sum(d["archives"] for d in decode.values())} archives over four sets, all byte for byte.')
    esc = sum(h['escapes_in_bit_parse'] for s in SETS for h in res[s]['headers'].values())
    if esc == 0:
        w(f'- **Escapes used:** {esc}. Every byte value in the test files also occurs in training, so the escape cost only its slot and one table byte.')
    else:
        w(f'- **Escapes used:** {esc}, each charged its code and eight raw bits.')
    w('')
    for metric, title in (('tokens', 'Tokens (exact minimum for each dictionary; percentage against BPE at the same cap)'),
                          ('bytes', 'Complete archive bytes (percentage against BPE at the same cap)')):
        w(f'## {title}')
        w('')
        w('| Cap | Rule | Slots used | ' + ' | '.join(SET_LABEL[s].capitalize() for s in SETS) + ' |')
        w('| ---: | --- | ---: | ' + ' | '.join('---:' for _ in SETS) + ' |')
        for cap in CAPS:
            for arm in ARMS:
                cells = []
                for s in SETS:
                    h, b = H(s, arm, cap), H(s, 'bpe', cap)
                    v = h['min_tokens'] if metric == 'tokens' else h['bytes']['complete']
                    r = b['min_tokens'] if metric == 'tokens' else b['bytes']['complete']
                    cells.append(n(v) if arm == 'bpe' else f'{n(v)} ({pct(v, r)})')
                w(f'| {n(cap)} | {LABEL[arm]} | {n(H("train", arm, cap)["slots_used_with_escape"])} | ' + ' | '.join(cells) + ' |')
        if metric == 'bytes':
            for z in (ZD, 'zstd-19 per file, no dictionary', ZS, 'zstd-19 one stream, trained 8 KiB dictionary'):
                w(f'| | {z} | | ' + ' | '.join(n(res[s]["zstd"]["rows"][z]["complete"]) for s in SETS) + ' |')
        w('')
    clusters = [set(line.split(',')) for line in (HERE / 'metadata' / 'ibm-identical-problem-clusters.txt').read_text().split()]
    earlier = {s: {f['unit'] for f in json.loads((HERE / 'frozen' / 'sets' / f'{s}.json').read_text())['files']} for s in ('train', 'dev')}
    dev_identical = sorted({p for c in clusters if c & earlier['train'] for p in c & earlier['dev']})
    w('Training and development columns are context. The development split had been scored by earlier runs, and IBM lists')
    w(f'{SMALL[len(dev_identical)]} of its problems as identical to training problems.')
    w('')
    w('## Paired comparisons')
    w('')
    w('Units are CodeNet problems or project files. "Lower / higher / tied" counts units where the first rule is lower.')
    w('')
    w('| Set | Cap | Comparison | Tokens | Lower / higher / tied | Sign test p | Payload bits | Lower / higher / tied |')
    w('| --- | ---: | --- | ---: | --- | ---: | ---: | --- |')
    for s in ('fresh', 'project'):
        for cap in CAPS:
            for a, b in (('token', 'bpe'), ('bytes', 'bpe'), ('bytes', 'token')):
                p = paired(s, cap, a, b)
                t, bits = p['tokens'], p['bits']
                w(f'| {SET_LABEL[s]} | {n(cap)} | {LABEL[a]} against {LABEL[b]} | {t["a_vs_b_percent"]:+.1f}% | '
                  f'{t["units_a_lower"]} / {t["units_a_higher"]} / {t["units_tied"]} | {t["sign_test_two_sided_p"]:.1g} | '
                  f'{bits["a_vs_b_percent"]:+.1f}% | {bits["units_a_lower"]} / {bits["units_a_higher"]} / {bits["units_tied"]} |')
    w('')
    w('## Which fragments pay their rent (4,096 cap)')
    w('')
    w('A fragment pays rent on a set if removing it, reparsing the files that used it with code lengths unchanged, and')
    w('recounting makes the complete archive larger. Fragments are grouped by how many training problems used them.')
    w('')
    w('| Rule | Training problems that used it | Fragments | Pay rent in training | Used on new problems | Pay rent on new problems | Net bytes on new problems | Pay rent on project | Net bytes on project |')
    w('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
    names = {'0': 'none', '1': 'one', '2-3': 'two or three', '4+': 'four or more'}
    for arm in ('token', 'bytes', 'bpe'):
        for c in ('0', '1', '2-3', '4+'):
            tr, fr, pj = (H(s, arm, 4096)['by_train_reuse_class'][c] for s in ('train', 'fresh', 'project'))
            if tr['entries']:
                w(f'| {LABEL[arm]} | {names[c]} | {n(tr["entries"])} | {n(tr["pays_rent"])} | {n(fr["used"])} | {n(fr["pays_rent"])} | '
                  f'{round(fr["rent_bits"] / 8):+,} | {n(pj["pays_rent"])} | {round(pj["rent_bits"] / 8):+,} |')
    w('')
    w('Dropping every fragment that fewer than two training problems used, and refitting the table on training files:')
    w('')
    w('| Rule | Fragments | Kept | ' + ' | '.join(f'{SET_LABEL[s].capitalize()}: tokens, archive' for s in SETS) + ' |')
    w('| --- | ---: | ---: | ' + ' | '.join('---:' for _ in SETS) + ' |')
    for arm in ('bpe', 'freq', 'length', 'token', 'bytes'):
        a = f'{arm}-K4096'
        cells = [f'{pct(res[s]["headers"][a + ".xp"]["min_tokens"], res[s]["headers"][a]["min_tokens"])}, '
                 f'{pct(res[s]["headers"][a + ".xp"]["bytes"]["complete"], res[s]["headers"][a]["bytes"]["complete"])}' for s in SETS]
        w(f'| {LABEL[arm]} | {n(res["fresh"]["headers"][a]["multi_byte_entries"])} | {n(res["fresh"]["headers"][a + ".xp"]["multi_byte_entries"])} | '
          + ' | '.join(cells) + ' |')
    w('')
    w('## Mechanism on the new problems')
    w('')
    w('| Cap | Rule | Fragments | Used | Overlapping matches | Uses in the parse | Repeats inside a file | Mean bytes per token |')
    w('| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |')
    for cap in CAPS:
        for arm in ARMS[1:]:
            h = H('fresh', arm, cap)
            r = h['reuse']
            w(f'| {n(cap)} | {LABEL[arm]} | {n(h["multi_byte_entries"])} | {n(r["multi_byte_entries_used"])} | '
              f'{n(h["candidate_multi_byte_matches_overlapping"])} | {n(h["realized_multi_byte_uses_min_token_parse"])} | '
              f'{100.0 * r["within_file_repeats"] / max(1, r["uses"]):.0f}% | {h["mean_realized_entry_length"]:.2f} |')
    w('')
    w('## Against zstd, by access contract (new problems)')
    w('')
    z = res['fresh']['zstd']['rows']

    def best_by(key):
        v, a, c = min((H('fresh', a, c)['bytes'][key], a, c) for a in ARMS[1:] for c in CAPS)
        return f'{n(v)} ({LABEL[a]} at {n(c)}, {n(H("fresh", a, c)["bytes"]["header"])} B header)'

    w('| Contract | Best BITS arm under that contract | zstd, trained 8 KiB dictionary, one frame per file | zstd, one stream, no dictionary |')
    w('| --- | ---: | ---: | ---: |')
    w(f'| Sequential, everything counted | {best_by("complete")} | {n(z[ZD]["complete"])} | {n(z[ZS]["complete"])} |')
    w(f'| Random access, index counted for both | {best_by("random_access_complete")} | {n(z[ZD]["random_access_complete"])} | not applicable |')
    w(f'| Dictionary already held by the reader | {best_by("dictionary_already_held")} | {n(z[ZD]["dictionary_already_held"])} | {n(z[ZS]["complete"])} |')
    w('')
    held = zc['dictionary_already_held']['fresh']
    held_header = res['fresh']['headers'][held['best_bits_dictionary']]['bytes']['header']
    need(held['best_bits'] < held['zstd_trained_dictionary'] and held_header >= 2 * 8192 and z[ZS]['complete'] < held['best_bits'],
         'the note under the access-contract table no longer matches the data; rewrite it')
    w('The last row is not a matched comparison: the BITS dictionary that wins it is several times larger than the 8 KiB')
    w('zstd dictionary, and one zstd stream with no dictionary is smaller than either.')
    w('')
    w('## What this does not show')
    w('')
    need(all(min(r['complete'] for r in res[s]['zstd']['rows'].values()) < min(h['bytes']['complete'] for h in res[s]['headers'].values()) for s in SETS),
         '"zstd beats it on every set" no longer matches the data; rewrite that line')
    w('- It is one training set, one entry length, two caps and five rules, scored once. Every dictionary is the outcome of a')
    w('  heuristic search; a token count is the exact minimum for that dictionary, not for the cap.')
    w('- The new problems come from the same collection as the training problems. The project is one repository in one language.')
    w('- The archive-bytes rule tries prefixes of two greedy orders. The rent measurement removes one fragment at a time with')
    w('  code lengths fixed, so it ignores interactions.')
    w('- The format is a flat list of strings and one static prefix code. zstd beats it on every set; nothing here claims a codec.')
    w('- The scorer was a second session of the same assistant under the same owner. Someone uninvolved still has to check the')
    w('  splits, the accounting, the decode and the wording before anything is posted.')

    outcomes = {'schema': 'gamma.bits-objective-holdout.rule-outcomes.v1',
                'source': 'make_results.py, from out/results-*.json; rules as written in PREREGISTRATION.md',
                'threshold_percent': THRESHOLD, 'decided_on': 'fresh', 'rules': rules,
                'context': {'development_problems_ibm_identical_to_training': dev_identical,
                            'escapes_used_on_any_set': esc,
                            'archives_decoded_byte_for_byte': sum(d['archives'] for d in decode.values())}}
    out_dir = Path(args.out) if args.out else None
    (out_dir or HERE).mkdir(parents=True, exist_ok=True)
    ((out_dir or HERE) / 'RESULTS.md').write_text('\n'.join(out) + '\n')
    ((out_dir or HERE / 'out') / 'rule-outcomes.json').write_text(json.dumps(outcomes, indent=1) + '\n')
    print('wrote RESULTS.md', len(out), 'lines, and rule-outcomes.json:', ' '.join(f'{k}={"holds" if v["holds"] else "fails"}' for k, v in rules.items()))


if __name__ == '__main__':
    main()
