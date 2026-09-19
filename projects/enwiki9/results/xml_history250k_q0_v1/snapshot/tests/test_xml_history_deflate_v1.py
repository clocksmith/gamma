"""Adversarial inversion, dictionary causality and exact census partitions."""
import random
import struct
import zlib

import pytest
from lib.coders import xml_history_deflate_v1 as c


@pytest.mark.parametrize('raw', [b'', b'\x00\xff<>"', bytes(range(256))*20,
    b'<page><title>Alpha</title><text>Alpha [[Beta]] &amp; 123 https://x/a</text><id>Alpha</id></page>',
    b'<text a=">">unterminated &amp; <tail', b'<text/>outside',
    random.Random(991).randbytes(7000), b'<text>'+b'abcd '*1800+b'</text>'])
def test_exact_inverse_repeat_and_costs(raw):
    for arm in c.ARMS:
        arc, enc = c.compress(raw, arm)
        decoded, dec = c.decompress(arc)
        assert decoded == raw and enc == dec
        assert c.compress(decoded, arm) == (arc, enc)
        assert sum(enc['costs'].values()) == len(arc)
    assert c.compress(raw, 'B') == c.compress(raw, 'K')


def test_partitions_and_completed_page_local_donors():
    raw = b'<page><title>Alpha</title><text>Alpha Beta</text><id>Beta</id></page><page><text>Alpha</text>'
    report = c.census(raw)
    assert sum(report['categories'].values()) == len(raw)
    assert sum(report['stream_bytes']) == len(raw)
    assert report['references']['xml_to_text']['hits'] == 1
    assert report['references']['text_to_xml']['hits'] == 1
    assert all(x['donor_end'] <= x['offset'] for x in report['reference_examples'])
    assert b''.join(x[3] for x in c.events(raw)) == raw
    assert report['categories']['prose_ascii_letters'] == len(b'AlphaBetaAlpha')


def test_no_future_reference_and_same_shifted_capacity():
    assert c.census(b'<page><text>Future</text><title>Future</title>')['references']['xml_to_text']['hits'] == 0
    history = [b'old1NEW2', b'own']
    actual, n = c.dictionary(history, 1, 'J')
    shifted, ns = c.dictionary(history, 1, 'S')
    assert n == ns == 4 and actual == b'ownNEW2' and shifted == b'ownold1'
    assert c.dictionary(history, 1, 'E') == (b'own', 0)
    # Encoder events may examine future syntax, but routing is transmitted and
    # dictionary construction depends only on these explicit emitted histories.
    assert c.dictionary(history, 1, 'J') == (actual, n)


def test_reject_truncation_trailing_and_decompression_bomb():
    arc, _ = c.compress(b'<text>hello</text>')
    for bad in [arc[:i] for i in range(len(arc))] + [arc+b'junk']:
        with pytest.raises((ValueError, zlib.error, struct.error)):
            c.decompress(bad)
    coder = zlib.compressobj(wbits=-15)
    bomb = coder.compress(b'A'*100000) + coder.flush()
    bad = c.HEADER.pack(b'XH01', b'B', 1, 1) + c.FRAME.pack(1, 1, len(bomb)) + bomb
    with pytest.raises(ValueError):
        c.decompress(bad)
