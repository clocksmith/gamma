"""Authored graph fixtures only; no source corpus or private cases."""
import copy
import unittest

from algsolve.synth import typed_word_codec as codec
from algsolve.synth import typed_program as base
from algsolve.synth import typed_vector_program as vector


def ref(name): return {'ref':name}
def lit(value): return {'literal':value}
def op(name,*args): return {'op':name,'args':list(args)}
def bind(name,value,kind='let'): return {'op':kind,'name':name,'value':value}
def call(name,out,*args): return {'op':'call','operator':name,'out':out,'args':list(args)}
def graph(inputs,body,result,output='int',schema=base.SCHEMA):
    return {'schema':schema,'parameters':list(inputs),'inputs':inputs,'body':body,'return':result,'output_type':output}


class TypedWordCodecTests(unittest.TestCase):
    def roundtrip(self,program,arguments,expected,profile='base-v2',recipes=None):
        ir=codec.runtime(profile)
        canonical=codec.canonicalize(program,profile,recipes)
        positional=[arguments[p] for p in program['parameters']]
        for width in (6,7,8):
            packet,cost=codec.encode(program,width,profile,recipes)
            decoded=codec.decode(packet)
            self.assertEqual(decoded,canonical)
            self.assertEqual(ir.execute(decoded,dict(zip(decoded['parameters'],positional))),expected)
            self.assertEqual(codec.execute(packet,positional),expected)
            self.assertEqual(ir.execute(program,arguments,recipes=recipes),expected)
            self.assertEqual(cost['packet_bits'],cost['payload_bits']+cost['framing_bits']+cost['padding_bits'])
            self.assertEqual(cost['payload_bits'],cost['selections']*width)
            self.assertEqual(cost['one_program_with_support_bits'],cost['packet_bits']+cost['dictionary_storage_bits']+cost['decoder_storage_bits']+cost['runtime_storage_bits'])
            self.assertLess(cost['padding_bits'],8)

    def test_branch_loop_cells_and_integer_constants(self):
        program=graph({'numbers':['list','int']},[
            bind('total',lit(-7),'var'),
            {'op':'for','item':'item','in':ref('numbers'),'body':[
                {'op':'if','condition':op('lt',lit(0),ref('item')),
                 'then':[bind('total',op('add',ref('total'),op('mul',ref('item'),lit(2))),'set')],
                 'else':[bind('total',op('sub',ref('total'),ref('item')),'set')]}]},
        ],ref('total'))
        self.roundtrip(program,{'numbers':[-3,0,4]},4)

    def test_resource_identity_heap_queue_map_dsu(self):
        program=graph({},[
            call('dsu.new','sets',lit(3)),call('dsu.union','joined',ref('sets'),lit(0),lit(1)),
            call('heap.new','heap'),call('heap.push','hpush',ref('heap'),lit(-5)),call('heap.pop','small',ref('heap')),
            call('queue.new','queue'),call('queue.push','qpush',ref('queue'),ref('small')),
            call('queue.pop','first',ref('queue')),call('map.new','mapping'),
            call('map.set','mset',ref('mapping'),lit(7),ref('first')),
            call('map.get','answer',ref('mapping'),lit(7),lit(19)),
        ],op('tuple',ref('joined'),ref('answer')),['tuple','bool','int'])
        self.roundtrip(program,{},(True,-5))

    def test_compound_types_sort_projection_and_boolean(self):
        program=graph({'pairs':['list',['tuple','int','int']]},[
            bind('ordered',op('sort_by',ref('pairs'),lit(1),lit(False))),
        ],op('tuple',op('len',ref('ordered')),op('not',lit(False))),['tuple','int','bool'])
        self.roundtrip(program,{'pairs':[[2,9],[1,-4]]},(2,True))

    def test_immutable_append_range_and_scoped_names(self):
        program=graph({'count':'int'},[bind('values',op('empty_ints'),'var'),
            {'op':'for','item':'index','in':op('range',ref('count')),'body':[
                bind('values',op('append',ref('values'),op('neg',ref('index'))),'set')]}],ref('values'),['list','int'])
        self.roundtrip(program,{'count':4},[0,-1,-2,-3])

    def test_vector_snapshot_is_charged_and_compatible(self):
        program=graph({},[call('vector.new','builder'),call('vector.append','first',ref('builder'),lit(4)),
            call('vector.snapshot','old',ref('builder')),call('vector.append','second',ref('builder'),lit(9)),
            call('vector.snapshot','new',ref('builder'))],op('tuple',ref('old'),ref('new')),
            ['tuple',['list','int'],['list','int']],vector.SCHEMA)
        self.roundtrip(program,{},([4],[4,9]),'vector-v1')
        self.assertEqual(len(codec.vocabulary('base-v2')),53)
        self.assertEqual(len(codec.vocabulary('vector-v1')),57)
        with self.assertRaises(ValueError): codec.encode(program,6,'base-v2')

    def test_recipes_expand_not_one_lookup_opcode(self):
        recipe=graph({'value':'int'},[],op('add',ref('value'),lit(3)))
        program=graph({'input':'int'},[{'op':'recipe','recipe':'authored_add','args':[ref('input')],'out':'result'}],ref('result'))
        self.roundtrip(program,{'input':8},11,recipes={'authored_add':recipe})
        canonical=codec.canonicalize(program,recipes={'authored_add':recipe})
        self.assertFalse(any(s['op']=='recipe' for s in canonical['body']))
        self.assertTrue(all('recipe' not in word for word in codec.vocabulary('base-v2')))

    def test_alpha_renaming_and_lexical_branch_hygiene(self):
        first=graph({'hello':'int'},[bind('result',op('add',ref('hello'),lit(2)))],ref('result'))
        second=graph({'world':'int'},[bind('other',op('add',ref('world'),lit(2)))],ref('other'))
        for width in (6,7,8): self.assertEqual(codec.encode(first,width)[0],codec.encode(second,width)[0])
        branches=graph({},[bind('value',lit(3),'var'),{'op':'if','condition':lit(True),
            'then':[bind('local',lit(5)),bind('value',ref('local'),'set')],
            'else':[bind('local',lit(6)),bind('value',ref('local'),'set')]}],ref('value'))
        self.roundtrip(branches,{},5)

    def test_unit_result_and_parameter_order_not_map_order(self):
        unit=graph({},[call('queue.new','queue'),call('queue.push','done',ref('queue'),lit(8))],ref('done'),'unit')
        self.roundtrip(unit,{},None)
        program=graph({'right':'int','left':'int'},[],op('sub',ref('left'),ref('right')))
        program['parameters']=['left','right']
        self.roundtrip(program,{'left':9,'right':4},5)
        canonical=codec.canonicalize(program)
        for width in (6,7,8):
            packet,_=codec.encode(program,width)
            self.assertEqual(codec.encode(codec.decode(packet),width)[0],packet)
            self.assertEqual(canonical['parameters'],['b0','b1'])

    def test_packet_execution_arity_budget_and_fresh_ownership(self):
        program=graph({'values':['list','int']},[bind('answer',op('append',ref('values'),lit(9)))],ref('answer'),['list','int'])
        empty=graph({},[],lit(7))
        for width in (6,7,8):
            packet,_=codec.encode(program,width)
            inputs=[[1,2]]; before=copy.deepcopy(inputs)
            result=codec.execute(packet,inputs)
            self.assertEqual(result,[1,2,9]); self.assertEqual(inputs,before)
            result.append(100)
            self.assertEqual(codec.execute(packet,inputs),[1,2,9])
            self.assertEqual(codec.execute(packet,[[]]),[9])
            for args in ([],[[1],[2]],{'values':[1]},'bad'):
                with self.assertRaises(codec.Invalid): codec.execute(packet,args)
            for budget in (0,-1,True,2000001):
                with self.assertRaises(codec.Invalid): codec.execute(packet,inputs,budget=budget)
            with self.assertRaises(codec.Invalid): codec.execute(packet,inputs,budget=1)
            constant,_=codec.encode(empty,width)
            self.assertEqual(codec.execute(constant,[]),7)

    def test_maximum_signed_integer_magnitudes_and_zero(self):
        for value in (0,1,-1,(1<<128)-1,-((1<<128)-1)):
            self.roundtrip(graph({},[],lit(value)),{},value)
        with self.assertRaises(ValueError): codec.encode(graph({},[],lit(1<<128)),6)

    def test_malformed_framing_padding_unused_and_trailing(self):
        for width in (6,7,8):
            packet,_=codec.encode(graph({},[],lit(2)),width)
            for bad in (b'',packet[:-1],packet+b'\0',b'BAD!'+packet[4:]):
                with self.assertRaises(codec.Invalid): codec.decode(bad)
            header=bytearray(packet); header[11]^=1
            with self.assertRaises(codec.Invalid): codec.decode(bytes(header))
            profile,w,words=codec._unpack(packet)
            with self.assertRaises(codec.Invalid): codec.decode(codec._packet(words+[0],w,profile))
            with self.assertRaises(codec.Invalid): codec.decode(codec._packet([63],w,profile))
            padding=codec.costs(packet)['padding_bits']
            if padding:
                broken=bytearray(packet); broken[-1]|=1
                with self.assertRaises(codec.Invalid): codec.decode(bytes(broken))

    def test_noncanonical_numerals_binding_and_type_rejection(self):
        packet,_=codec.encode(graph({},[],lit(2)),6)
        profile,width,words=codec._unpack(packet); vocab=codec.vocabulary(profile); codes={w:i for i,w in enumerate(vocab)}
        # Parameter count zero begins immediately after PROGRAM.
        bad=words[:1]+[codes['BIT0']]+words[1:]
        with self.assertRaises(codec.Invalid): codec.decode(codec._packet(bad,width,profile))
        bad=list(words); sign=bad.index(codes['POS']); bad[sign]=codes['NEG']; bad[sign+1:]=[codes['BIT0'],codes['END']]
        with self.assertRaises(codec.Invalid): codec.decode(codec._packet(bad,width,profile))
        malformed=graph({'x':'int'},[],ref('x'))
        canonical=codec.canonicalize(malformed); canonical['return']={'ref':'b99'}
        with self.assertRaises(codec.Invalid): codec.decode(codec._packet(codec._encode_words(canonical,profile),6,profile))
        canonical['return']=lit(True)
        with self.assertRaises(codec.Invalid): codec.decode(codec._packet(codec._encode_words(canonical,profile),6,profile))

    def test_bounded_decode_counts_and_nesting(self):
        vocab=codec.vocabulary('base-v2'); codes={w:i for i,w in enumerate(vocab)}
        # Overlong numerical token stream must fail before constructing a graph.
        bad=[codes['PROGRAM']]+[codes['BIT1']]*129+[codes['END']]
        with self.assertRaises(codec.Invalid): codec.decode(codec._packet(bad,6,'base-v2'))
        # Zero inputs, followed by an excessively nested output type.
        bad=[codes['PROGRAM'],codes['BIT0'],codes['END']]+[codes['T:list']]*50+[codes['T:int']]
        with self.assertRaises(codec.Invalid): codec.decode(codec._packet(bad,6,'base-v2'))
        packet,_=codec.encode(graph({},[],lit(2)),6); fields=list(codec.HEADER.unpack(packet[:codec.HEADER.size])); fields[4]=codec.MAX_WORDS+1
        with self.assertRaises(codec.Invalid): codec.decode(codec.HEADER.pack(*fields)+packet[codec.HEADER.size:])


if __name__=='__main__': unittest.main()
