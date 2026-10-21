#!/usr/bin/env python3
"""MIT; see CODE_LICENSE.txt. Reproduce frozen packets, never execute solutions."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
CODEC_SHA256 = '64585df01200488e834540986f8ef99703dd99cecc76808a2b9654e1ea318afe'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def load_json(name):
    return json.loads((BASE / name).read_text(encoding='utf-8'))


def main():
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument('--output', type=Path,
                           help='Optional new directory for reproduced packets and receipt; must not exist.')
    args = arguments.parse_args()
    if args.output is not None:
        check(not args.output.exists(), '--output must be a new directory')
        check(not args.output.is_symlink(), '--output must not be a symlink')
    files = load_json('FILES.json')['files']
    for name, pin in files.items():
        path = BASE / name
        check(path.resolve().is_relative_to(BASE), 'file path escapes package')
        check(not path.is_symlink(), 'package symlinks are unsupported')
        raw = path.read_bytes()
        check(digest(raw) == pin['sha256'] and len(raw) == pin['bytes'], 'file hash mismatch: ' + name)
    codec_path = BASE / 'literal_codec.py'
    check(digest(codec_path.read_bytes()) == CODEC_SHA256, 'frozen codec hash mismatch')
    spec = importlib.util.spec_from_file_location('readable_frozen_codec', codec_path)
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    contract = load_json('reproduction-contract.json')
    check(contract['codec_sha256'] == CODEC_SHA256, 'contract codec mismatch')
    qualification = load_json('qualification.json')
    source_pins = {(str(row['problem_id']), row['language']): row['source_sha256']
                   for row in qualification['rows']}
    result_rows = []
    artifacts = []
    rejected = []

    def rejects(label, packet, dictionary, literals):
        try:
            codec.verify_packet(packet, dictionary, literals, b'')
        except (AssertionError, ValueError, IndexError, UnicodeError):
            rejected.append(label)
            return
        raise ValueError('malformed packet accepted: ' + label)

    for expected in contract['rows']:
        language = expected['language']
        width = expected['width']
        profile_path = BASE / 'profiles' / (language + '-6-small-statements')
        dictionary = (profile_path / 'dictionary.ltd').read_bytes()
        check(digest(dictionary) == expected['dictionary_sha256'], 'dictionary hash mismatch')
        literals = codec.decode_dictionary(dictionary)
        check(len(literals) == expected['entries'] <= 2 ** width, 'dictionary cardinality mismatch')
        json_literals = json.loads((profile_path / 'dictionary.json').read_text())['literals']
        check(literals == [entry['text'].encode('utf-8') for entry in json_literals], 'dictionary ID mismatch')
        packets_bytes = selection_bits = padding_bits = framing_bits = 0
        for problem_id, program in expected['programs'].items():
            suffix = '.js' if language == 'javascript' else '.py'
            source = (profile_path / 'assembled' / (problem_id + suffix)).read_bytes()
            check(digest(source) == program['source_sha256'] == source_pins[(problem_id, language)],
                  'qualified source mismatch')
            sequence, missing = codec.parse(source, literals)
            check(sequence == program['sequence'] and not missing, 'optimal segmentation mismatch')
            packet = codec.packet(sequence, width, dictionary)
            codec.verify_packet(packet, dictionary, literals, source)
            check(digest(packet) == program['packet_sha256'], 'preserved packet hash mismatch')
            check(len(packet) == program['packet_bytes'], 'packet size mismatch')
            if width == 6:
                check(packet == (profile_path / 'programs' / (problem_id + '.ltv')).read_bytes(),
                      'stored six-bit packet mismatch')
            check(8 * len(packet) == program['selection_bits'] + program['padding_bits'] + program['framing_bits'],
                  'bit accounting mismatch')
            packets_bytes += len(packet)
            selection_bits += program['selection_bits']
            padding_bits += program['padding_bits']
            framing_bits += program['framing_bits']
            label = language + '-' + str(width) + '-' + problem_id
            artifacts.append((label + '.ltv', packet))
            invalid = bytearray(packet)
            invalid[5] ^= 1
            rejects(label + '-wrong-hash', bytes(invalid), dictionary, literals)
            rejects(label + '-truncated', packet[:-1], dictionary, literals)
            rejects(label + '-trailing', packet + b'\0', dictionary, literals)
            rejects(label + '-unused-ID', codec.packet([len(literals)], width, dictionary), dictionary, literals)
            if program['padding_bits']:
                invalid = bytearray(packet)
                invalid[-1] |= 1
                rejects(label + '-nonzero-padding', bytes(invalid), dictionary, literals)
        check(packets_bytes == expected['packet_bytes'], 'aggregate packet bytes mismatch')
        check(len(dictionary) + packets_bytes == expected['package_bytes'], 'aggregate package bytes mismatch')
        check(selection_bits == expected['selection_bits'] and padding_bits == expected['padding_bits']
              and framing_bits == expected['framing_bits'], 'aggregate bit accounting mismatch')
        result_rows.append({'language': language, 'width': width, 'programs': 3,
                            'dictionary_sha256': digest(dictionary), 'selection_bits': selection_bits,
                            'padding_bits': padding_bits, 'framing_bits': framing_bits,
                            'packet_bytes': packets_bytes, 'dictionary_bytes': len(dictionary),
                            'dictionary_plus_packet_bytes': len(dictionary) + packets_bytes})
    report = {'schema': 'gamma.readable-literals.packaged-reproduction-receipt.v1',
              'codec_sha256': CODEC_SHA256, 'package_manifest_sha256': digest((BASE / 'FILES.json').read_bytes()),
              'packets_verified': len(artifacts), 'source_programs': 6,
              'widths': [6, 7, 8], 'malformed_controls_rejected': len(rejected),
              'candidate_source_execution': False, 'new_qualification': False,
              'rows': result_rows}
    if args.output is not None:
        args.output.mkdir(parents=True, exist_ok=False)
        for name, packet in artifacts:
            (args.output / name).write_bytes(packet)
        (args.output / 'receipt.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
