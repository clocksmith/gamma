"""verify.py with post-freeze packet checks; verify.py itself stays as frozen.

1. bitpack.decode returns text, whereas verify.py compared it with source bytes; encode
   the decoded text to UTF-8 before comparing.
2. When dictionary.ltd is present (including Experiment C escape packets), unpack its
   LTD1 entries and assert they match manifest['vocabulary'] (the exact list checked
   for rule W/U eligibility)."""
import json
import struct

import verify
from bitpack import decode


def _unpack_ltd1(raw):
    if raw[:4] != b'LTD1' or len(raw) < 8:
        raise ValueError('LTD1 header')
    count, at, entries = struct.unpack_from('>I', raw, 4)[0], 8, []
    for _ in range(count):
        size = struct.unpack_from('>I', raw, at)[0]
        entries.append(raw[at + 4:at + 4 + size].decode('utf-8'))
        at += 4 + size
    if at != len(raw):
        raise ValueError('LTD1 length')
    return entries


verify.ltv_decode = lambda dictionary, packet: decode(dictionary, packet).encode('utf-8')
_orig_check_job = verify.check_job


def _checked_job(folder, texts, hashes):
    report = _orig_check_job(folder, texts, hashes)
    dict_path = folder / 'dictionary.ltd'
    if dict_path.exists():
        m = json.loads((folder / 'manifest.json').read_text())
        unpacked = _unpack_ltd1(dict_path.read_bytes())
        assert unpacked == m['vocabulary'], 'dictionary.ltd differs from eligibility-checked vocabulary'
    return report


verify.check_job = _checked_job

if __name__ == '__main__':
    verify.main()
