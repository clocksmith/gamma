"""Source-bound incumbent admission and monotonic retention, encoding only."""
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import math
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
OBJECTIVE = ['maximize_coverage', 'minimize_selections', 'minimize_full_package_bytes']
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


core = module('incumbent_core', HERE.parent / 'reachable_core.py')
codec = module('incumbent_codec', HERE.parent.parent / 'readable-v1/literal_codec.py')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def table_bytes(strings):
    pieces = [s.encode('ascii') for s in strings]
    return b'LTD1' + len(pieces).to_bytes(4, 'big') + b''.join(len(p).to_bytes(4, 'big') + p for p in pieces)


def validate_table(strings, sources, pool, width):
    require(type(width) is int and width in [7, 8], 'width outside frozen successor')
    require(strings and len(strings) == len(set(strings)) <= 2 ** width, 'entry cap / duplicate / empty table')
    require(all(type(p) is str and p and p.isascii() for p in strings), 'invalid literal')
    require(set(strings) <= set(pool), 'literal outside frozen candidate pool')
    require(not set(strings).intersection(s for vs in sources.values() for s in vs.values()), 'whole-program entry')


def validate_payload(descriptor, expected, manifest, dictionary, packets, sources, pool, fixed_choices):
    """Reject incompatible claims, check every imported assembly, then resegment.

    A descriptor binds an audited historical result to today's same source pool.
    This function receives data; it never imports or runs solution source.
    """
    began = time.process_time()
    for key in ['language', 'width', 'cohort_sha256', 'pool_sha256', 'problem_ids', 'objective']:
        require(descriptor.get(key) == expected[key], 'incumbent identity mismatch: ' + key)
    require(expected['objective'] == OBJECTIVE, 'objective mismatch')
    require(expected['problem_ids'] == sorted(sources, key=int), 'problem denominator mismatch')
    require(set(fixed_choices) == set(sources), 'fixed source choices incomplete')
    width = expected['width']
    strings = [p.decode('ascii') for p in codec.decode_dictionary(dictionary)]
    validate_table(strings, sources, pool, width)
    require(strings == sorted(strings), 'noncanonical dictionary ID ordering')
    require(manifest['language'] == expected['language'] and manifest['width'] == width, 'manifest language / width')
    require(manifest['policy'] == 'compression' and manifest['arm'] == 'dictionary-only', 'incumbent is not the fixed-source comparator')
    require(manifest['dictionary_sha256'] == sha(dictionary), 'dictionary hash mismatch')
    require(manifest['entries'] == len(strings), 'entry count mismatch')
    require(manifest['whole_program_entries'] == 0 and manifest['implicit_helpers_imports_wrappers_or_operands'] == 0, 'unaccounted source')
    programs = manifest['programs']
    require(len(programs) == len(sources) and {p['problem_id'] for p in programs} == set(sources), 'missing / duplicate problem')
    require(set(packets) == set(sources), 'packet denominator mismatch')
    fixed_sources = {}
    for p in programs:
        pid = p['problem_id']
        require(p['represented'] is True, 'incomplete incumbent coverage')
        variant = p['variant']
        require(variant == fixed_choices[pid] and variant in sources[pid], 'unqualified or mismatched source variant')
        source = sources[pid][variant].encode('ascii')
        require(sha(source) == p['source_sha256'] and len(source) == p['source_bytes'], 'source hash / length mismatch')
        packet = packets[pid]
        require(len(packet) >= 41 and packet[4] == width, 'packet width mismatch')
        codec.verify_packet(packet, dictionary, [s.encode('ascii') for s in strings], source)
        count = int.from_bytes(packet[37:41], 'big')
        bits = ''.join(format(b, '08b') for b in packet[41:])
        ids = [int(bits[i * width:(i + 1) * width], 2) for i in range(count)]
        require(ids == p['sequence'] and count == p['selections'], 'sequence mismatch')
        require(sha(packet) == p['packet_sha256'] and len(packet) == p['packet_bytes'], 'packet hash / length mismatch')
        require(p['selection_bits'] == count * width and p['framing_bits'] == 328 and p['padding_bits'] == (-count * width) % 8, 'packet accounting mismatch')
        fixed_sources[pid] = {variant: sources[pid][variant]}
    fixed = core.evaluate(fixed_sources, strings, width, mandatory=())
    require(core.audit(fixed_sources, fixed, width), 'fixed-source exact parse audit')
    for key in ['coverage', 'denominator', 'uncovered', 'selections', 'dictionary_bytes', 'packet_bytes', 'package_bytes']:
        require(fixed[key] == manifest[key], 'incumbent metric mismatch: ' + key)
    for p in programs:
        require(len(fixed['parsed'][(p['problem_id'], p['variant'])]) == p['selections'], 'nonminimal incumbent assembly')
    require(fixed['coverage'] == len(sources), 'incumbent does not cover full cohort')
    joint = core.evaluate(sources, strings, width, mandatory=())
    require(core.audit(sources, joint, width), 'all-source exact parse audit')
    require(core.cost(joint) <= core.cost(fixed), 'source reselection lost feasible incumbent')
    return joint, {'prior_fixed_cost': list(core.cost(fixed)), 'resegmented_joint_cost': list(core.cost(joint)),
                   'same_source_pool': True, 'packet_checks': len(programs), 'exact_source_resegmentation': True,
                   'source_executions': 0, 'dictionary_sha256': sha(dictionary),
                   'validation_cpu_seconds': time.process_time() - began,
                   'additional_backward_variant_parses': len(fixed_sources) + sum(map(len, sources.values())),
                   'additional_forward_variant_checks': len(fixed_sources) + sum(map(len, sources.values()))}


def read_pin(pin):
    raw = Path(pin['path']).read_bytes()
    require(sha(raw) == pin['sha256'], 'artifact hash mismatch: ' + pin['path'])
    return raw


def read_json_pin(pin):
    raw = read_pin(pin)
    decoded = gzip.decompress(raw) if pin.get('encoding') == 'gzip' else raw
    if 'decoded_sha256' in pin:
        require(sha(decoded) == pin['decoded_sha256'], 'decoded artifact hash mismatch')
    return json.loads(decoded)


def load_incumbent(descriptor, expected, sources, pool, fixed_choices):
    manifest = read_json_pin(descriptor['manifest'])
    require(manifest['label'] == descriptor['label'], 'incumbent label mismatch')
    audit = read_json_pin(descriptor['audit'])
    require(audit['status'] == 'passed', 'independent incumbent audit did not pass')
    audited = [r for r in audit['results'] if r['label'] == descriptor['label']]
    require(len(audited) == 1, 'incumbent absent from audit')
    for key in ['coverage', 'denominator', 'selections', 'package_bytes', 'entries']:
        require(audited[0][key] == manifest[key], 'audit / manifest mismatch: ' + key)
    packets = {pid: read_pin(pin) for pid, pin in descriptor['packets'].items()}
    return validate_payload(descriptor, expected, manifest, read_pin(descriptor['dictionary']), packets,
                            sources, pool, fixed_choices)


class MonotonicBest:
    """Only admissible, freshly resegmented states can displace the incumbent."""
    def __init__(self, sources, pool, width, incumbent):
        self.sources, self.pool, self.width = sources, pool, width
        self.best = None
        self.history = []
        self.cpu_seconds = 0.0
        self.resegmentation_calls = 0
        self.consider(incumbent, 'audited-incumbent')

    def consider(self, state, origin):
        began = time.process_time()
        validate_table(state['vocab'], self.sources, self.pool, self.width)
        verified = core.evaluate(self.sources, state['vocab'], self.width, mandatory=())
        require(core.comparable(verified) == core.comparable(state), 'stale / forged search state')
        previous = core.cost(self.best) if self.best is not None else None
        accepted = previous is None or core.cost(verified) < previous
        if accepted:
            self.best = verified
        require(previous is None or core.cost(self.best) <= previous, 'best-result regression')
        self.history.append({'origin': origin, 'candidate_cost': list(core.cost(verified)),
                             'retained_cost': list(core.cost(self.best)), 'accepted': accepted,
                             'dictionary_sha256': sha(table_bytes(verified['vocab']))})
        self.resegmentation_calls += 1
        self.cpu_seconds += time.process_time() - began
        return self.best


def search_with_incumbent(sources, pool, width, incumbent, optimizer, expired, *, max_rounds, max_trials):
    keeper = MonotonicBest(sources, pool, width, incumbent)
    trajectory, detail = optimizer(sources, incumbent, pool, {}, width, expired,
        max_rounds=max_rounds, max_trials=max_trials, observe=keeper.consider)
    keeper.consider(trajectory, 'returned-trajectory')
    require(core.cost(keeper.best) <= core.cost(incumbent), 'lost imported incumbent')
    began = time.process_time()
    require(core.audit(sources, keeper.best, width), 'retained state exact parse audit')
    retention = {'history': keeper.history, 'cpu_seconds': keeper.cpu_seconds,
        'resegmentation_calls': keeper.resegmentation_calls,
        'additional_backward_variant_parses': keeper.resegmentation_calls * sum(map(len, sources.values())),
        'final_forward_variant_checks': sum(map(len, sources.values())),
        'final_forward_audit_cpu_seconds': time.process_time() - began,
        'optimizer_cpu_includes_observer_checks': True,
        'counts_are_not_search_trials': True}
    return keeper.best, trajectory, detail, retention
