import copy
import time
import unittest
from algsolve.synth import typed_fragments as f, typed_codec, typed_program as ir


def program(inputs, body, answer, output='int'):
    return dict(schema=ir.SCHEMA,parameters=list(inputs),inputs=inputs,body=body,
                **{'return':answer},output_type=output)


def pair(g, uid='fixture:1'):
    target=typed_codec.encode(g,'fixture')
    return dict(uid=uid,problem_family=uid,learning_split='development_fit',
                graph_sha256=typed_codec.digest(target),target=target,input={'statement':'count values then add one'})


def fixture_index():
    g=program({'nums':['list','int']},[
        {'op':'let','name':'n','value':{'op':'len','args':[{'ref':'nums'}]}}],
        {'op':'add','args':[{'ref':'n'},{'literal':1}]})
    return f.build_index([pair(g)])


class FragmentTests(unittest.TestCase):
    def test_nonfit_or_changed_source_is_rejected(self):
        g=program({'x':'int'},[],{'op':'add','args':[{'ref':'x'},{'literal':1}]})
        for split in ('development_audit','protected'):
            p=pair(g);p['learning_split']=split
            with self.assertRaises(ValueError):f.build_index([p])
        p=pair(g);p['target']['program']['return']['args'][1]['literal']=2
        with self.assertRaises(ValueError):f.build_index([p])

    def test_external_mutation_and_resource_capture_fail(self):
        with self.assertRaisesRegex(ir.Invalid,'external cell'):
            f.close_fragment([{'op':'set','name':'x','value':{'literal':1}}],{'ref':'x'},{'x':'int'})
        with self.assertRaisesRegex(ir.Invalid,'capture a resource'):
            f.close_fragment([{'op':'call','operator':'map.get','args':[{'ref':'m'},{'ref':'x'},{'literal':0}],'out':'n'}],{'ref':'n'},{'m':'map_int_int','x':'int'})

    def test_owned_resources_work_but_never_escape(self):
        body=[{'op':'call','operator':'map.new','args':[],'out':'m'},
              {'op':'call','operator':'map.set','args':[{'ref':'m'},{'ref':'x'},{'literal':9}],'out':'stored'},
              {'op':'call','operator':'map.get','args':[{'ref':'m'},{'ref':'x'},{'literal':0}],'out':'n'}]
        closed,roles=f.close_fragment(body,{'ref':'n'},{'x':'int'})
        self.assertEqual(ir.execute(closed,{'input0':5}),9)
        self.assertEqual(ir.execute(closed,{'input0':7}),9)
        with self.assertRaises(ir.Invalid):f.close_fragment(body,{'ref':'m'},{'x':'int'})

    def test_branch_local_cannot_escape_and_resource_aliases_fail(self):
        with self.assertRaises((ir.Invalid,KeyError)):
            f.close_fragment([{'op':'if','condition':{'literal':True},'then':[{'op':'let','name':'x','value':{'literal':1}}],'else':[]}],{'ref':'x'},{})
        with self.assertRaises(ir.Invalid):
            f.close_fragment([{'op':'call','operator':'map.new','args':[],'out':'m'},
                              {'op':'let','name':'alias','value':{'ref':'m'}}],{'literal':0},{})

    def test_two_piece_assembly_preserves_constants_and_hygiene(self):
        index=fixture_index();before=copy.deepcopy(index)
        length=next(x for x in index['fragments'] if x['program']['body']==[] and x['operations']=={'len':1})
        add=next(x for x in index['fragments'] if x['operations']=={'add':1})
        term={'fragment':add['id'],'args':[{'fragment':length['id'],'args':[{'input':'values'}]}]}
        g,trace=f.assemble(term,{'values':['list','int']},'int',index)
        self.assertEqual(ir.execute(g,{'values':[4,5,6]}),4)
        self.assertEqual(len(trace),2);self.assertEqual(index,before)
        with self.assertRaises(ir.Invalid):f.assemble(term,{'values':'bool'},'int',index)
        broken=copy.deepcopy(index);broken['fragments'][0]['program']['output_type']='bool'
        bad={'fragment':broken['fragments'][0]['id'],'args':[]}
        with self.assertRaisesRegex(ir.Invalid,'content changed'):f.assemble(bad,{},'int',broken)

    def test_same_space_bounded_deterministic_order_and_expired_deadline(self):
        index=fixture_index()
        results=[]
        for guided in (False,True):
            stats={'expansions':0,'candidates':0}
            values=list(f.candidates(index,{'values':['list','int']},'int','count values then add one',guided,stats,time.perf_counter()+2))
            results.append({typed_codec.digest(v) for v in values})
            self.assertLessEqual(stats['candidates'],128);self.assertLessEqual(stats['expansions'],2048)
        self.assertEqual(*results)
        stats={'expansions':0,'candidates':0}
        self.assertEqual(list(f.candidates(index,{'values':['list','int']},'int','',True,stats,time.perf_counter()-1)),[])
        self.assertEqual(stats,{'expansions':0,'candidates':0})

    def test_whole_graph_and_constant_only_fragment_excluded(self):
        g=program({'x':'int'},[],{'op':'add','args':[{'ref':'x'},{'literal':1}]})
        self.assertEqual(f.build_index([pair(g)])['fragments'],[])


if __name__=='__main__':unittest.main()
