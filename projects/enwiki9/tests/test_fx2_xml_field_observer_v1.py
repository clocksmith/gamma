"""Synthetic differential checks against the retained Python WRT inverse."""
import os
from pathlib import Path
import random
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import wrt_exact as wrt

WORDS = [b'a'] * 44880
for index, word in ((0,b'title'),(1,b'id'),(80,b'timestamp'),(3919,b'username'),
                    (3920,b'comment'),(44879,b'text')):
    WORDS[index] = word
MARKERS = (b'<title>',b'</title>',b'<id>',b'</id>',b'<timestamp>',b'</timestamp>',
           b'<username>',b'</username>',b'<comment>',b'</comment>',
           b'<text xml:space="preserve">',b'</text>')


def swap(data):
    return bytes(map(wrt.wrt_byte_transform, data))


class Tests(unittest.TestCase):
    def run_native(self, modeled, raw_size):
        return subprocess.run([os.environ['FX2_XML_OBSERVER_BINARY'],modeled.hex(),str(raw_size)],
                              capture_output=True, text=True, timeout=5)

    def compare(self, code):
        # Oracle parses complete events; its outputs are released only at end.
        provisional = bytes([7]) + (0).to_bytes(4,'big') + bytes([7]) + swap(code)
        # Determine exact raw size independently using the inverse's state API.
        state = wrt.WrtDecoderState(); raw = bytearray(); i = 0
        while i < len(code):
            c=code[i]; i+=1
            if c==12: raw.extend(state.escaped(code[i])); i+=1
            elif c in (6,7,64): state.control(c)
            elif c>=128:
                token=bytearray([c])
                if c>207:
                    token.append(code[i]); i+=1
                    if token[-1]>207: token.append(code[i]); i+=1
                raw.extend(state.word(WORDS[wrt.token_index(token)]))
            else: raw.extend(state.literal(c))
        stored=provisional[:1]+len(raw).to_bytes(4,'big')+provisional[5:]
        parsed=wrt.parse_store_bytes(stored,WORDS)
        modeled=stored[5:]
        result=self.run_native(modeled,len(raw))
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,self.run_native(modeled,len(raw)).stdout)
        events={event.end-5:event.decoded for event in parsed.events}
        rows=result.stdout.splitlines(); self.assertEqual(len(rows),len(modeled))
        accumulated=bytearray(); field=0
        for end,row in enumerate(rows,1):
            actual_field, emitted, snapshot=row.split(' ')
            decoded=events.get(end,b'')
            self.assertEqual(bytes.fromhex(emitted),decoded)
            for byte in decoded:
                accumulated.append(byte)
                for index,marker in enumerate(MARKERS):
                    if accumulated.endswith(marker): field=0 if index%2 else index//2+1
            self.assertEqual(int(actual_field),field,(end,bytes(accumulated)))
            self.assertEqual(len(bytes.fromhex(snapshot)),66)
        self.assertEqual(accumulated,raw)
        return rows

    def test_native_rejections_and_state(self):
        result=subprocess.run([os.environ['FX2_XML_OBSERVER_BINARY']],capture_output=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_all_fields_literal_and_dictionary_tokens(self):
        self.compare(b'<title>a</title><id>12</id><timestamp>x</timestamp>'
                     b'<username>x</username><comment>x</comment>'
                     b'<text xml:space="preserve">x</text>')
        self.compare(b'<\x80>x</\x80><\x81>1</\x81><\xd0\x80>x</\xd0\x80>'
                     b'<\xff\xcf>x</\xff\xcf><\xf0\xd0\x80>x</\xf0\xd0\x80>'
                     b'<\xff\xef\xcf xml:space="preserve">x</\xff\xef\xcf>')

    def test_case_escapes_and_no_entity_expansion(self):
        self.compare(b'<\x40\x80>x</\x80><text xml:space="preserve">'
                     b'&lt;title&gt;\x07ab\x06\x40z\x0c\xff\x40\x0c!a'
                     b'\x07\x40\x80</text>')

    def test_partial_markers_and_malformed_markup_are_literal(self):
        self.compare(b'<title>x</titleX><<id>2</id>\0\x0c\xff<title')
        self.compare(b'<text xml:space="preserve" >x<TITLE>y</TITLE>')

    def test_random_synthetic_events(self):
        rng=random.Random(20260909)
        pieces=[b'a',b' ',b'\n',b'<title>',b'</title>',b'\x80',b'\xd0\x80',
                b'\xf0\xd0\x80',b'\x07',b'\x06',b'\x40',b'\x0c\xff',b'\x0c\0']
        for _ in range(12): self.compare(b''.join(rng.choice(pieces) for _ in range(100)))

    def test_truncated_and_invalid_codes(self):
        for code in (b'\x0c',b'\xd0',b'\xf0\xd0',b'\xd0\0',b'\xd0\xd0',
                     b'\xf0\xf0',b'\xf0\xd0\xff'):
            with self.subTest(code=code):
                self.assertNotEqual(self.run_native(b'\7'+swap(code),1).returncode,0)

    def test_event_completion_is_causal(self):
        rows=self.compare(b'<\xf0\xd0\x80>x</\xf0\xd0\x80>')
        self.assertEqual([int(row.split(' ')[0]) for row in rows[:6]],[0,0,0,0,0,5])


if __name__=='__main__': unittest.main()
