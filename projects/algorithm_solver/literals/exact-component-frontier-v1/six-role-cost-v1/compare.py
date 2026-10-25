"""Matched source-pool costs under an unchanged, hash-verified dictionary.

The recovery backend is trusted, pinned research code, never candidate code.
Capture its successful function-return state without editing historical files.
Candidate source strings are only segmented and decoded, never executed here.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys

RECOVERY_SHA = 'cac4ff4686c69c462ed629610e02ce1693c9d4a1d29bffa7866d2d9e4f85ec0a'
DICTIONARY_SHA = '8931fe373986246b4f95210423daa4c104d6dd9d549beea44a4ae93ef14b6d4d'
CHOICES_SHA = '820b7b4416ad70444aba3fd49b360e7de63859fd94557c5a0f95c724dbda01f6'


def capture_return(function, *args, **kwargs):
    """Observe only this trusted function's return; restore prior profiler."""
    previous = sys.getprofile()
    if previous is not None:
        raise RuntimeError('do not replace an existing profiler')
    captured = {}

    def observe(frame, event, arg):
        if event == 'return' and frame.f_code is function.__code__:
            captured.update(frame.f_locals)

    try:
        sys.setprofile(observe)
        function(*args, **kwargs)
    finally:
        sys.setprofile(previous)
    if not captured:
        raise ValueError('trusted recovery did not return state')
    return captured


def recover(path, output):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != RECOVERY_SHA:
        raise ValueError('historical recovery code identity')
    # Its sibling classifier is separately checked before import.
    classifier = Path(path).parent / 'classify.py'
    if hashlib.sha256(classifier.read_bytes()).hexdigest() != '5b7912aaab1164aeaaa0968831e1dcdffb2c391731546a1792dd49366e2980da':
        raise ValueError('recovery classifier identity')
    sys.path.insert(0, str(Path(path).parent))
    spec = importlib.util.spec_from_file_location('pinned_six_role_cost_recovery', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with contextlib.redirect_stdout(io.StringIO()):
        state = capture_return(module.main, str(output), 'JS-GLOBAL-RESULT-v3.json', long_mode='paired')
    if state['report']['status'] != 'exact_frozen_incumbent_attributed_no_search':
        raise ValueError('recovery incomplete or failed')
    best = state['best']
    if (module.digest(best['vocabulary']) != DICTIONARY_SHA or
            module.digest(best['choices']) != CHOICES_SHA or
            (best['metrics']['selections'], best['metrics']['characters']) != (35086, 14892)):
        raise ValueError('current full-pool incumbent identity')
    state['f'] = module.f
    return module, state


def choose(groups, rows, references):
    chosen = {}
    for problem, keys in groups.items():
        reachable = [key for key in keys if rows[key] is not None]
        if not reachable:
            raise ValueError('covered problem became unreachable')
        chosen[problem] = min(reachable, key=lambda key: (
            rows[key]['selections'], rows[key]['characters'],
            key != references[problem], key))
    return chosen


def whole_source_exclusion(source, vocabulary):
    """Retain the current owner's complete-source/body containment exclusion."""
    compact = lambda value: ''.join(value.split())
    banned = {compact(source)}
    match = re.search(r'function\s+solve\s*\([^)]*\)\s*\{', source)
    if match and source.rfind('}') >= match.end():
        banned.add(compact(source[match.end():source.rfind('}')]))
    banned.discard('')
    if any(part in compact(literal) for part in banned for literal in vocabulary):
        raise ValueError('unchanged dictionary contains a complete new source/body')


def compare(state, additions):
    """Add separately qualified exact bytes; preserve every original variant.

    additions: {format|role: {problem: {key, source, sha256}}}. Qualification
    verification belongs to the caller and must precede source materialization.
    """
    f = state['f'] if 'f' in state else None
    if f is None:
        raise ValueError('explicit independent codec owner required')
    best, original_texts = state['best'], state['texts']
    vocabulary = best['vocabulary']
    groups = state['groups']
    references = state['references']
    if len(groups) != 300 or len(original_texts) != 875:
        raise ValueError('full fixed source-pool denominator')
    new_texts = {}
    for arm, variants in additions.items():
        if arm not in ('format', 'role'):
            raise ValueError('undeclared arm')
        for pid, item in variants.items():
            if pid not in groups or item['key'] in original_texts or item['key'] in new_texts:
                raise ValueError('new source identity collision')
            if hashlib.sha256(item['source'].encode()).hexdigest() != item['sha256']:
                raise ValueError('qualified source byte identity')
            whole_source_exclusion(item['source'], vocabulary)
            new_texts[item['key']] = item['source']
    rows = dict(best['rows'])
    rows.update(state['accelerator'].Graph(new_texts).score(vocabulary, materialize=True))
    texts = dict(original_texts, **new_texts)
    decoded = {}
    results = {}
    for label, arms in (('original_pool', ()), ('plus_format', ('format',)),
                        ('plus_role', ('role',)), ('plus_both', ('format', 'role'))):
        active = {pid: list(keys) for pid, keys in groups.items()}
        for arm in arms:
            for pid, item in additions[arm].items():
                active[pid].append(item['key'])
        choices = choose(active, rows, references)
        selected, variants = {}, {}
        for pid, key in choices.items():
            if key not in decoded:
                decoded[key] = f.exact_path(texts[key], vocabulary)
            path = decoded[key]
            if path is None or path[:2] != (rows[key]['selections'], rows[key]['characters']):
                raise ValueError('independent byte/codepoint segmentation mismatch')
            selected[pid] = (key, path)
            variants[pid] = {key: texts[key]}
        metrics = f.metrics(vocabulary, selected, variants, 8)
        # Do not publish literal support or source strings from this private return.
        metrics.pop('support')
        if label == 'original_pool' and (metrics['selections'], metrics['characters'], metrics['package_bytes']) != (35086, 14892, 57502):
            raise ValueError('actual original packet/package accounting')
        results[label] = dict(metrics=metrics, choices=choices,
                             variant_count=sum(map(len, active.values())),
                             source_pool_utf8_bytes=sum(len(texts[k].encode()) for keys in active.values() for k in keys),
                             selected_source_utf8_bytes=sum(len(texts[k].encode()) for k in choices.values()),
                             changed_owners=sorted(pid for pid in groups if choices[pid] != best['choices'][pid]))
    return results
