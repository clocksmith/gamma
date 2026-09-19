"""Exact byte events and a bounded causal-history diagnostic codec.

XH01 transmits each event's stream, raw length and Deflate length. Routing is
paid side information, not an inference from future decoder bytes. Both streams
retain 32768 emitted bytes. Cross dictionaries use the newest n opposite bytes;
the shifted control uses the preceding n, n=min(16384,len(opposite)//2).
All dictionary bytes precede the current event. This is a diagnostic Deflate
profile, not the project's native predictor or a prize delivery package.
"""
import hashlib
import re
import struct
import zlib

MAX_RAW = 250000
MAX_ARCHIVE = 8000000
BLOCK = 4096
HEADER = struct.Struct('<4scII')
FRAME = struct.Struct('<BII')
ARMS = 'PBKXEJS'
TAG = re.compile(rb'<(?:!--[\s\S]*?--|!\[CDATA\[[\s\S]*?\]\]|(?:[^>\"\']|\"[^\"]*\"|\'[^\']*\')*)>')
NAME = re.compile(rb'<\s*(/?)\s*([A-Za-z_:][A-Za-z0-9_:.-]*)')
TOKEN = re.compile(rb'https?://[^\s<>\[\]{}]+|&(?:#[xX][0-9a-fA-F]+|#[0-9]+|[A-Za-z][A-Za-z0-9]*);|[0-9]+|[\[\]{}|=*\'#]+|[A-Za-z]+|[^\x00-\x7f]+|[\s\S]')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def events(raw):
    """Lossless lexical routing; incomplete/unknown syntax remains literal.

    XML tags are stream 0; bytes within a complete <text> opener are stream 1.
    This is not language identification or validating XML parsing. The archive
    explicitly transmits routing, including decisions made by this encoder.
    """
    if len(raw) > MAX_RAW:
        raise ValueError('population exceeds bounded profile')
    pos, in_text = 0, False
    for match in TAG.finditer(raw):
        if pos < match.start():
            yield pos, int(in_text), 'content' if in_text else 'metadata', raw[pos:match.start()]
        value = match.group()
        yield match.start(), 0, 'xml_syntax', value
        name = NAME.match(value)
        if name and name[2] == b'text':
            in_text = not bool(name[1]) and not value.rstrip().endswith(b'/>')
        pos = match.end()
    if pos < len(raw):
        yield pos, int(in_text), 'content' if in_text else 'metadata', raw[pos:]


def census(raw):
    categories = {k: 0 for k in ('xml_syntax', 'metadata', 'prose_ascii_letters',
        'wiki_markup', 'entities', 'urls', 'numbers', 'non_ascii', 'content_other')}
    streams = [0, 0]
    words = [{}, {}]
    references = {'xml_to_text': {'eligible_words': 0, 'hits': 0, 'bytes': 0},
                  'text_to_xml': {'eligible_words': 0, 'hits': 0, 'bytes': 0}}
    witness, examples = hashlib.sha256(), []
    spans = []
    for offset, stream, kind, data in events(raw):
        streams[stream] += len(data)
        spans.append({'offset': offset, 'bytes': len(data), 'stream': stream, 'kind': kind})
        if kind == 'xml_syntax':
            categories[kind] += len(data)
            # Page-local reference vocabulary; syntax itself is never a donor.
            if re.fullmatch(rb'<page\s*>', data):
                words = [{}, {}]
            continue
        for token in TOKEN.finditer(data):
            value, start = token.group(), offset + token.start()
            if stream == 0:
                category = 'metadata'
            elif value.startswith((b'http://', b'https://')):
                category = 'urls'
            elif value.startswith(b'&') and len(value) > 1:
                category = 'entities'
            elif value.isdigit():
                category = 'numbers'
            elif value[:1] in b'[]{}|=*\'#':
                category = 'wiki_markup'
            elif value.isalpha():
                category = 'prose_ascii_letters'
            elif value[0] >= 128:
                category = 'non_ascii'
            else:
                category = 'content_other'
            categories[category] += len(value)
            if value.isalpha() and len(value) >= 3:
                row = references['xml_to_text' if stream else 'text_to_xml']
                row['eligible_words'] += 1
                if value in words[1-stream]:
                    donor_end = words[1-stream][value]
                    assert donor_end <= start
                    row['hits'] += 1
                    row['bytes'] += len(value)
                    record = f'{stream}:{start}:{donor_end}:'.encode() + value + b'\n'
                    witness.update(record)
                    if len(examples) < 16:
                        examples.append({'stream': stream, 'offset': start, 'donor_end': donor_end,
                                         'word': value.decode('ascii')})
                # Fixed FIFO of 128 distinct completed exact-spelling words.
                words[stream].setdefault(value, start + len(value))
                if len(words[stream]) > 128:
                    del words[stream][next(iter(words[stream]))]
    assert sum(categories.values()) == sum(streams) == len(raw)
    return {'raw_bytes': len(raw), 'raw_sha256': sha(raw), 'stream_bytes': streams,
            'categories': categories, 'references': references, 'spans': spans,
            'reference_examples': examples, 'reference_witness_sha256': witness.hexdigest(),
            'scope': 'opening development prefix; content is not proof of English language',
            'reference_policy': 'page-local FIFO128 exact ASCII words length>=3; completed donors only',
            'cost_attribution': 'Separate actual Deflate payloads; no native predictor entropy claim'}


def dictionary(history, stream, arm):
    own, other = history[stream], history[1-stream]
    enabled = arm in 'JS' or (arm == 'X' and stream == 1) or (arm == 'E' and stream == 0)
    n = min(16384, len(other)//2) if enabled else 0
    donor = other[-2*n:-n] if arm == 'S' and n else other[-n:] if n else b''
    return own[-(32768-n):] + donor, n


def _report(raw, archive, costs, witness, cross_events):
    return {'raw_bytes': len(raw), 'raw_sha256': sha(raw), 'archive_bytes': len(archive),
            'archive_sha256': sha(archive), 'costs': costs, 'cross_events': cross_events,
            'witness_sha256': witness.hexdigest(),
            'witness_coverage': 'event stream, lengths, dictionary bytes, emitted raw bytes; not zlib internal state'}


def _observe(witness, stream, data, dictionary_bytes):
    witness.update(struct.pack('<BII', stream, len(data), len(dictionary_bytes)))
    witness.update(dictionary_bytes)
    witness.update(data)


def compress(raw, arm='J'):
    if arm not in ARMS or len(arm) != 1 or len(raw) > MAX_RAW:
        raise ValueError('invalid arm or population bound')
    arm = 'B' if arm == 'K' else arm
    parts = [(0, raw)] if arm == 'P' else [(s, d[i:i+BLOCK]) for _, s, _, d in events(raw)
                                          for i in range(0, len(d), BLOCK)]
    archive = bytearray(HEADER.pack(b'XH01', arm.encode(), len(raw), len(parts)))
    history, costs, witness, cross_events = [b'', b''], {'framing': HEADER.size, 'xml_payload': 0, 'text_payload': 0}, hashlib.sha256(), [0, 0]
    for stream, data in parts:
        zd, n = (b'', 0) if arm == 'P' else dictionary(history, stream, arm)
        coder = zlib.compressobj(6, zlib.DEFLATED, -15, zdict=zd)
        payload = coder.compress(data) + coder.flush()
        archive.extend(FRAME.pack(stream, len(data), len(payload)))
        archive.extend(payload)
        costs['framing'] += FRAME.size
        costs['text_payload' if stream else 'xml_payload'] += len(payload)
        cross_events[stream] += bool(n)
        _observe(witness, stream, data, zd)
        history[stream] = (history[stream] + data)[-32768:]
    archive = bytes(archive)
    return archive, _report(raw, archive, costs, witness, cross_events)


def decompress(archive):
    if not HEADER.size <= len(archive) <= MAX_ARCHIVE:
        raise ValueError('invalid archive bound')
    magic, encoded_arm, length, count = HEADER.unpack_from(archive)
    arm = encoded_arm.decode('ascii')
    if magic != b'XH01' or arm not in 'PBXEJS' or length > MAX_RAW or count > MAX_RAW + 1:
        raise ValueError('invalid header')
    if arm == 'P' and count != 1:
        raise ValueError('invalid unsplit frame count')
    pos, output, history = HEADER.size, bytearray(), [b'', b'']
    costs, witness, cross_events = {'framing': HEADER.size, 'xml_payload': 0, 'text_payload': 0}, hashlib.sha256(), [0, 0]
    for _ in range(count):
        if pos + FRAME.size > len(archive):
            raise ValueError('truncated frame')
        stream, size, packed = FRAME.unpack_from(archive, pos)
        pos += FRAME.size
        if stream not in (0, 1) or (arm == 'P' and stream != 0) or size > (MAX_RAW if arm == 'P' else BLOCK) or len(output)+size > length or pos+packed > len(archive):
            raise ValueError('invalid frame bound')
        zd, n = (b'', 0) if arm == 'P' else dictionary(history, stream, arm)
        decoder = zlib.decompressobj(-15, zdict=zd)
        data = decoder.decompress(archive[pos:pos+packed], size+1)
        if len(data) != size or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError('invalid deflate frame')
        pos += packed
        costs['framing'] += FRAME.size
        costs['text_payload' if stream else 'xml_payload'] += packed
        cross_events[stream] += bool(n)
        _observe(witness, stream, data, zd)
        output.extend(data)
        history[stream] = (history[stream] + data)[-32768:]
    if pos != len(archive) or len(output) != length:
        raise ValueError('trailing bytes or wrong raw length')
    raw = bytes(output)
    return raw, _report(raw, archive, costs, witness, cross_events)
