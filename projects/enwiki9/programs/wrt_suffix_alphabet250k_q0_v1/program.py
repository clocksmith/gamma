#!/usr/bin/env python3
"""Fixed dictionary-only word alphabet; no corpus fitting or new vocabulary."""
import hashlib
import re

def transform(data, arm):
    words = re.findall(rb'[a-z]+', data)
    assert b'\n'.join(words)+b'\n' == data
    assert len(words) == len(set(words)) and 3920 < len(words) <= 44880
    result = words[:80]
    for band in (words[80:3920], words[3920:]):
        if arm == 'D':
            band = sorted(band, key=lambda w: (w[::-1], w))
        elif arm == 'S':
            band = sorted(band, key=lambda w: (hashlib.sha256(b'wrt-suffix-alphabet-v1\0'+w).digest(), w))
        elif arm not in ('P', 'K'):
            raise ValueError(arm)
        result.extend(band)
    assert result[:80] == words[:80]
    assert set(result[80:3920]) == set(words[80:3920])
    assert set(result[3920:]) == set(words[3920:])
    return b'\n'.join(result)+b'\n'
