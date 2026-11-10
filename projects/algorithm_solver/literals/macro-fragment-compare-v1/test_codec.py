import itertools
import unittest
import sys
from unittest.mock import patch
from functools import lru_cache
import codec
import shapes

class CodecTests(unittest.TestCase):
    def test_exact_segmentation_against_exhaustive_oracle(self):
        table=((b'ab',),(b'ba',),(b'aaa',))
        for width in (6,7,8):
            for n in range(1,8):
                for values in itertools.product(b'ab',repeat=n):
                    raw=bytes(values)
                    @lru_cache(None)
                    def oracle(i):
                        if i==len(raw):return 0
                        values=[width+9*(j-i)+1+oracle(j) for j in range(i+1,len(raw)+1)]
                        values += [width+oracle(i+len(p[0])) for p in table if raw.startswith(p[0],i)]
                        return min(values)
                    bits,_=codec.Encoder(raw,table,width).encode()
                    self.assertEqual(len(bits),oracle(0))
                    decoded,stats=codec.unpack(codec.packet(bits,width),table,width)
                    self.assertEqual(decoded,raw)
    def test_nested_macros_charge_operands_and_concat(self):
        raw=b'f(ababa)+f(ababa)';table=((b'f(',b')'),(b'',b'+',b''),(b'ab',),(b'a',))
        occ=[(0,8,table[0],((2,7),)),(9,17,table[0],((11,16),)),(0,17,table[1],((0,8),(9,17)))]
        bits,_=codec.Encoder(raw,table,6,occ).encode();out,stats=codec.decode(bits,table,6)
        self.assertEqual(out,raw);self.assertGreater(stats['macro_calls'],0)
        self.assertGreater(stats['concat_count_bits'],0)
        self.assertEqual(len(bits),stats['primary_selections']*6+stats['spelling_payload_bits']+stats['transition_bits']+stats['concat_count_bits'])
    def test_nesting_boundary_roundtrips_at_every_width(self):
        table = ((b'(', b')'),)
        for width in (6, 7, 8):
            for nesting in (codec.MAX_DEPTH, codec.MAX_DEPTH + 1):
                raw = b'(' * nesting + b'x' + b')' * nesting
                occurrences = [(i, len(raw)-i, table[0], ((i+1, len(raw)-i-1),))
                               for i in range(nesting)]
                bits, _ = codec.Encoder(raw, table, width, occurrences).encode()
                self.assertEqual(codec.decode(bits, table, width)[0], raw)
                # At most MAX_DEPTH shells can surround the innermost spelling.
                expected = codec.MAX_DEPTH * width + width + 1 + 9 * (1 + 2 * (nesting-codec.MAX_DEPTH))
                self.assertEqual(len(bits), expected)

    def test_concat_consumes_its_own_depth(self):
        table = ((b'f(', b')'), (b'ab',), (b'cd',))
        raw = b'f(abcd)'
        occurrences = [(0, len(raw), table[0], ((2, 6),))]
        for width in (6, 7, 8):
            count_bits = ((16 + width - 1) // width) * width
            for limit in (1, 2):
                with patch.object(codec, 'MAX_DEPTH', limit):
                    bits, _ = codec.Encoder(raw, table, width, occurrences).encode()
                    decoded, stats = codec.decode(bits, table, width)
                    self.assertEqual(decoded, raw)
                    expected = 2 * width + 37 if limit == 1 else 4 * width + count_bits
                    self.assertEqual(len(bits), expected)
                    self.assertEqual(stats['count_words'], 0 if limit == 1 else count_bits // width)

    def test_depth_constrained_cost_against_independent_oracle(self):
        table = ((b'f(', b')'), (b'ab',), (b'cd',))
        for width in (6, 7, 8):
            for nesting in (1, 2, 3):
                raw = b'f(' * nesting + b'abcd' + b')' * nesting
                occurrences = [(2*i, len(raw)-i, table[0], ((2*i+2, len(raw)-i-1),))
                               for i in range(nesting)]
                for limit in (0, 1, 2, 3):
                    @lru_cache(None)
                    def options(start, end, depth):
                        values = [(stop, width+9*(stop-start)+1, True)
                                  for stop in range(start+1, end+1)]
                        for parts in table:
                            if len(parts) == 1 and raw.startswith(parts[0], start) and start+len(parts[0]) <= end:
                                values.append((start+len(parts[0]), width, False))
                        if depth < limit:
                            for a, b, parts, holes in occurrences:
                                if a == start and b <= end:
                                    values.append((b, width+sum(single(x, y, depth+1) for x, y in holes), False))
                        return values

                    @lru_cache(None)
                    def sequences(start, end, depth, previous_raw=False):
                        if start == end:
                            return {0: 0}
                        costs = {}
                        for stop, cost, is_raw in options(start, end, depth):
                            if previous_raw and is_raw:
                                continue
                            for count, suffix in sequences(stop, end, depth, is_raw).items():
                                costs[count+1] = min(costs.get(count+1, float('inf')), cost+suffix)
                        return costs

                    @lru_cache(None)
                    def single(start, end, depth):
                        best = min(cost for stop, cost, _ in options(start, end, depth) if stop == end)
                        if depth < limit:
                            overhead = width + ((16+width-1)//width)*width
                            for count, cost in sequences(start, end, depth+1).items():
                                if count >= 2:
                                    best = min(best, overhead+cost)
                        return best

                    expected = min(sequences(0, len(raw), 0).values())
                    with patch.object(codec, 'MAX_DEPTH', limit):
                        bits, _ = codec.Encoder(raw, table, width, occurrences).encode()
                        self.assertEqual(len(bits), expected)
                        self.assertEqual(codec.decode(bits, table, width)[0], raw)

    def test_iterative_encoder_and_explicit_state_budget(self):
        raw = b'(' * 110 + b'x' + b')' * 110
        table = ((b'(', b')'),)
        occurrences = [(i, len(raw)-i, table[0], ((i+1, len(raw)-i-1),)) for i in range(110)]
        old_limit = sys.getrecursionlimit()
        try:
            sys.setrecursionlimit(200)
            bits, _ = codec.Encoder(raw, table, 6, occurrences).encode()
        finally:
            sys.setrecursionlimit(old_limit)
        self.assertEqual(codec.decode(bits, table, 6)[0], raw)
        encoder = codec.Encoder(raw, table, 6, occurrences)
        with patch.object(codec, 'MAX_DP_STATES', 32):
            with self.assertRaisesRegex(ValueError, 'Optimizer state limit'):
                encoder.encode()
        self.assertFalse(encoder._cache)
        self.assertEqual(codec.decode(encoder.encode()[0], table, 6)[0], raw)
        raw = b'x' * codec.MAX_BYTES
        bits, _ = codec.Encoder(raw, (), 8).encode()
        self.assertEqual(codec.decode(bits, (), 8)[0], raw)

    def test_unicode_and_exact_integer_bytes(self):
        raw='return 900719925474099312345 + len("猫")\n'.encode()
        for width in (6,7,8):
            bits,_=codec.Encoder(raw,(),width).encode()
            self.assertEqual(codec.unpack(codec.packet(bits,width),(),width)[0],raw)
    def test_malformed_packets(self):
        table=((b'left',b'right'),)
        for bits in ['1','000010','000011','0000000','000001'+'0'*18]:
            with self.assertRaises(ValueError):codec.decode(bits,table,6)
        bits,_=codec.Encoder(b'x',(),6).encode();p=codec.packet(bits,6)
        for bad in [p+b'\0',p[:-1],p[:-1]+bytes([p[-1]|1])]:
            with self.assertRaises(ValueError):codec.unpack(bad,(),6)
    def test_sequence_canonicality_and_count_words(self):
        for width in (6,7,8):
            code=lambda n:format(n,f'0{width}b')
            countbits=((16+width-1)//width)*width
            raw=codec.spelling(b'x',width)
            concat=code(1)+format(2,f'0{countbits}b')+code(3)+code(3)
            table=((b'f(',b')'),(b'x',))
            for bits in [concat,raw+raw,code(2)+code(1)+format(2,f'0{countbits}b')+concat+code(3),
                         code(2)+code(1)+format(2,f'0{countbits}b')+raw+raw]:
                with self.assertRaises(ValueError):codec.decode(bits,table,width)
            out,stats=codec.decode(code(2)+concat,table,width)
            self.assertEqual(out,b'f(xx)')
            self.assertEqual(stats['count_words'],countbits//width)
            self.assertEqual(stats['primary_selections'],4)
    def test_duplicate_sources_do_not_create_reuse(self):
        source='def solve(x):\n y = x + 12\n return y * 3\n'
        values={'1':source,'2':source};meta={k:shapes.python_shape(v) for k,v in values.items()}
        literals,macros,_,_,_=shapes.mine(values,meta)
        self.assertEqual(literals,[]);self.assertEqual(macros,[])
    def test_original_body_exclusion_survives_compact_pool(self):
        sources={'1':'def solve(a):\n x = a + 1\n return x\n','2':'def solve(b):\n x = b + 1\n return x\n'}
        meta={k:shapes.python_shape(v) for k,v in sources.items()}
        literals,_,_,_,_=shapes.mine(sources,meta,{b'x = a + 1'})
        self.assertTrue(all(b'x = a + 1' not in x for x in literals))
    def test_spelling_cost_oracle_agrees_with_existing_codec(self):
        import run
        fragments=['aa'+str(i) for i in range(63)]
        sources={'1':'aaa0 aa1 900719925474099312345 猫','2':'aa8aa32aa5'}
        expected=sum(len(run.FSP.packet_bytes(run.FSP.encode(s,fragments,6)))*8 for s in sources.values())
        import select_literals
        self.assertEqual(select_literals.packet_score(sources,[x.encode() for x in fragments],6),expected)
    def test_source_owner_and_proper_holes(self):
        with self.assertRaises(ValueError):codec.Encoder(b'abc',((b'a',b'c'),),6,[(0,3,(b'a',b'c'),((0,3),))])
        with self.assertRaises(ValueError):codec.Encoder(b'abc',((b'a',b'd'),),6,[(0,3,(b'a',b'd'),((1,2),))])
    def test_single_operand_beats_charged_concat(self):
        for width in (6,7,8):
            table=((b'ab',),(b'cd',),(b'abcd',))
            encoder=codec.Encoder(b'abcd',table,width)
            self.assertEqual(encoder.single(0,4),(width,('entry',4)))
            encoder=codec.Encoder(b'abcd',table[:2],width)
            cost,token=encoder.single(0,4)
            concat_overhead=width+((16+width-1)//width)*width
            self.assertEqual(cost,min(2*width+concat_overhead,width+9*4+1))
            self.assertEqual(token[0],'concat')
            encoder.encode()
    def test_empty_shells_and_short_concat_rejected(self):
        for width in (6,7,8):
            with self.assertRaises(ValueError):codec.validate(((b'',b'\n',b''),),width)
            for count in (0,1):
                bits=format(2,f'0{width}b')+format(1,f'0{width}b')+format(count,f'0{((16+width-1)//width)*width}b')
                with self.assertRaises(ValueError):codec.decode(bits,((b'f(',b')'),),width)
    def test_js_arrow_method_and_class_units_excluded(self):
        sources={'a':'class A {} const f=x=>x+1; const o={m(x){return x+2;}};',
                 'b':'class A {} const f=y=>y+1; const o={m(y){return y+2;}};'}
        metadata,_=shapes.shapes(sources,'javascript')
        literals,_,occ,banned,_=shapes.mine(sources,metadata)
        self.assertNotIn(b'class A {}',literals)
        for pid,items in occ.items():
            raw=sources[pid].encode()
            for start,end,_,_ in items:self.assertNotIn(raw[start:end].strip(),banned)
        for text in (b'class A {}',b'x+1',b'return x+2;'):
            self.assertIn(text,banned)
    def test_shapes_preserve_unicode_offsets_and_exclude_whole_body(self):
        sources={'a':'def solve(x):\n return x + "猫"\n','b':'def solve(y):\n return y + "猫"\n'}
        meta={k:shapes.python_shape(s) for k,s in sources.items()}
        literals,macros,occ,banned,support=shapes.mine(sources,meta)
        self.assertNotIn(b'return x + "\xe7\x8c\xab"',literals)
        for pid,items in occ.items():
            raw=sources[pid].encode()
            for a,b,parts,holes in items:
                value=parts[0]
                for (x,y),suffix in zip(holes,parts[1:]):value+=raw[x:y]+suffix
                self.assertEqual(value,raw[a:b])

if __name__=='__main__':unittest.main()
