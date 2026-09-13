#!/usr/bin/env python3
"""Article-local alias opportunity census; no changed predictor or codec claim."""
from array import array
from bisect import bisect_left
from pathlib import Path
import hashlib
import json
import math
import re
import struct
import sys

DEFINITION = re.compile(rb"([A-Z][A-Za-z'-]*(?: [A-Za-z][A-Za-z'-]*){1,5}) \(([A-Z]{2,6})\)")
STOP = {b'a', b'an', b'and', b'for', b'in', b'of', b'on', b'the', b'to'}
WINDOW = 8
MAX_ALIASES = 16


def definitions(raw):
    rows = []
    for match in DEFINITION.finditer(raw):
        words = match[1].split(b' ')
        for first in range(len(words) - 1):
            suffix = words[first:]
            initials = b''.join(word[:1].upper() for word in suffix if word.lower() not in STOP)
            name = b' '.join(suffix)
            if initials == match[2] and len(name) <= 96:
                rows.append((match.end(), match[2], name))
                break
    return rows


def census(raw, stream, boundary):
    """Only completed definitions and fully observed donor windows are usable.

    Offline indexing finds event locations; each event uses raw[:position] and
    prior state only. A target starts at the WRT boundary after an ASCII space
    following a recognized surface form. The latest window per literal label
    is retained; an unfinished latest window supplies no donor.
    """
    events = [(m.end(), 0, None) for m in re.finditer(rb'<page>', raw)]
    events += [(end, 1, (alias, name)) for end, alias, name in definitions(raw)]
    events += [(m.end(), 2, None) for m in re.finditer(rb' ', raw)]
    events.sort(key=lambda row: (row[0], row[1]))
    aliases, disabled, histories = {}, set(), {}
    counts = dict(recognized_definitions=0, installed_definitions=0, duplicate_definitions=0,
                  ambiguous_aliases=0, capacity_rejections=0, article_resets=0,
                  recognized_mentions=0, unavailable_boundaries=0)
    opportunities = {'D': [], 'S': []}
    installed = []
    article = 0
    for position, kind, value in events:
        if kind == 0:
            aliases.clear(); disabled.clear(); histories.clear()
            counts['article_resets'] += 1
            article += 1
            continue
        if kind == 1:
            alias, name = value
            counts['recognized_definitions'] += 1
            if alias in disabled:
                continue
            if alias in aliases:
                if aliases[alias] == name:
                    counts['duplicate_definitions'] += 1
                else:
                    aliases.pop(alias); disabled.add(alias)
                    histories.pop(alias, None)
                    counts['ambiguous_aliases'] += 1
                continue
            if len(aliases) + len(disabled) >= MAX_ALIASES:
                counts['capacity_rejections'] += 1
                continue
            aliases[alias] = name
            counts['installed_definitions'] += 1
            installed.append(dict(article=article, available_after_raw=position,
                                  alias=alias.decode('ascii'), full_name=name.decode('ascii')))
            continue
        if not aliases:
            continue
        labels = sorted(set(aliases) | set(aliases.values()), key=lambda label: (-len(label), label))
        label = None
        for candidate in labels:
            start = position - len(candidate) - 1
            if start < 0 or raw[start:position] != candidate + b' ':
                continue
            if start and (65 <= raw[start-1] <= 90 or 97 <= raw[start-1] <= 122 or 48 <= raw[start-1] <= 57 or raw[start-1] == 95):
                continue
            label = candidate
            break
        if label is None:
            continue
        counts['recognized_mentions'] += 1
        target = boundary(position)
        if target is None or target + WINDOW > len(stream):
            counts['unavailable_boundaries'] += 1
            continue
        names = sorted(set(aliases.values()))
        shuffled = {alias: names[(names.index(name) + 1) % len(names)] for alias, name in aliases.items()}
        for arm, relation in [('D', aliases), ('S', shuffled)]:
            if arm == 'S' and len(names) < 2:
                continue
            donors = [relation[label]] if label in relation else [alias for alias, name in relation.items() if name == label]
            candidates = [(histories[donor], donor) for donor in donors
                          if donor in histories and histories[donor] + WINDOW <= target]
            if not candidates:
                continue
            donor, donor_label = max(candidates)
            expected = stream[donor:donor+WINDOW]
            observed = stream[target:target+WINDOW]
            prefix = 0
            for left, right in zip(expected, observed):
                if left != right:
                    break
                prefix += 1
            opportunities[arm].append(dict(article=article, available_after_raw=position,
                target_wrt=target, donor_wrt=donor, window_bytes=WINDOW,
                surface=label.decode('ascii'), donor_surface=donor_label.decode('ascii'),
                matching_prefix_bytes=prefix, exact_window_match=expected == observed))
        histories[label] = target
    return dict(counts=counts, installed_definitions=installed, opportunities=opportunities,
                control_note='S changes abbreviation-to-name edges among currently known names. With fewer than two distinct names its comparison is unavailable, never an assumed failure.')


def analyze(raw_path, store_path, dictionary_path, trace_path):
    from wrt_exact import parse_store
    parsed = parse_store(Path(store_path), Path(dictionary_path))
    raw = Path(raw_path).read_bytes()
    if parsed.decoded != raw:
        raise ValueError('WRT inverse does not equal bound raw input')
    trace = Path(trace_path).read_bytes()
    rows = struct.unpack_from('<Q', trace, 8)[0]
    if trace[:8] != b'CMX21P1\0' or len(trace) != 16 + 2 * rows or rows != 8 * len(parsed.stream):
        raise ValueError('P1 trace format or WRT coordinate mismatch')
    probabilities = array('H'); probabilities.frombytes(trace[16:])
    if sys.byteorder != 'little':
        probabilities.byteswap()
    if any(p == 0 for p in probabilities):
        raise ValueError('Illegal probability')
    raw_ends, stream_ends = array('I'), array('I')
    offset = 0
    for event in parsed.events:
        offset += len(event.decoded)
        raw_ends.append(offset); stream_ends.append(event.end)
    def boundary(position):
        index = bisect_left(raw_ends, position)
        return stream_ends[index] if index < len(raw_ends) and raw_ends[index] == position else None
    result = census(raw, parsed.stream, boundary)
    for arm, windows in result['opportunities'].items():
        covered = set()
        for window in windows:
            covered.update(range(window['target_wrt'], window['target_wrt'] + WINDOW))
        loss = 0.0
        for byte in sorted(covered):
            for bit in range(8):
                p = probabilities[8 * byte + bit]
                truth_probability = p if (parsed.stream[byte] >> (7-bit)) & 1 else 65536 - p
                loss -= math.log2(truth_probability / 65536)
        result[arm] = dict(opportunity_windows=len(windows), distinct_wrt_bytes=len(covered),
                           parent_ideal_bits_in_union=loss,
                           exact_donor_window_matches=sum(row['exact_window_match'] for row in windows),
                           matching_prefix_bytes=sum(row['matching_prefix_bytes'] for row in windows))
    result.update(schema='gamma.enwiki9.alias-residual-opportunity.v1', scopeBytes=len(raw),
                  raw_population='[0,1000000)', wrt_bytes=len(parsed.stream), trace_rows=rows,
                  input_sha256=hashlib.sha256(raw).hexdigest(), exact_wrt_inverse=True,
                  all_donors_precede_targets=all(row['donor_wrt'] + WINDOW <= row['target_wrt'] for rows in result['opportunities'].values() for row in rows),
                  actual_archive_savings_bytes=None, actual_predictive_gain_bits=None,
                  complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
                  interpretation='Parent log loss in a union of causal windows is an optimistic ideal-payload opportunity ceiling for changes confined to those windows. It is not achieved gain, an exact finite-archive bound, or a full-corpus estimate. Donor agreement is descriptive; no new predictor is run.')
    return result


if __name__ == '__main__':
    if len(sys.argv) != 6:
        raise SystemExit('usage: alias_residual_opportunity_v1.py RAW STORE DICTIONARY TRACE OUTPUT')
    result = analyze(*sys.argv[1:5])
    Path(sys.argv[5]).write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
