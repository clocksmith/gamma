"""Invented independent-report ban batching and exact trace equivalence."""
import copy
import json
import os
from pathlib import Path
import resource
import subprocess
import tempfile
import time
import unittest

import common as c
import engine
import report
import parser_adapter
from ban_replay import BanReplay

TEXT = 'function solve(a){return a+a}'
HELPER = Path(__file__).resolve().parents[1]/'tail-search-v1/structure.cjs'


def variants(texts):
    return {pid+':'+c.sha(text.encode()): text for pid, text in texts.items()}


class BanReplayTests(unittest.TestCase):
    def test_actual_service_receipt_bytes_and_phase_prefix_reconcile(self):
        resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2)
        config={'parser':{'implementation_sha256':parser_adapter.implementation(),
                         'limits':dict(parser_adapter.LIMITS)},
                'limits':{'address_space_bytes':8*1024**3},
                'arm_cores':{'24':sorted(os.sched_getaffinity(0))}}
        vocab=c.p.ALPHABET
        menu={'names':['aa'], 'contexts':[{'pattern':['return ',None,'+',None,'']}]}
        deadline=time.monotonic()+30
        previous=None;cache=BanReplay(HELPER,deadline)
        with tempfile.TemporaryDirectory() as tmp:
            for phase,texts in [('fit',{'2':TEXT}),('validation',{'3':TEXT})]:
                start=time.monotonic();path=Path(tmp)/(phase+'.json')
                with parser_adapter.Session(phase,deadline,path,config):
                    got=engine.apply(texts,vocab,menu,None if previous is None else previous['ledger'])
                end=time.monotonic()
                got.update(anchor='24',started_monotonic=start,finished_monotonic=end,
                           worker_seconds=end-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
                if phase=='fit':got['anchor_deadline']=deadline
                cache.extend(got['ledger']['variants']);receipt=json.loads(path.read_text())
                checked=report.parser_receipt(receipt,phase,got,config,cache,previous)
                self.assertGreater(checked['requests_completed'],0)
                for key in ('requests_completed','request_bytes_total','response_bytes_total'):
                    bad=copy.deepcopy(receipt);bad[key]+=1
                    with self.assertRaises(AssertionError):report.parser_receipt(bad,phase,got,config,cache,previous)
                previous=got

    def test_batched_scalar_identity_and_incremental_phase(self):
        texts = {str(i): TEXT.replace('a+a', f'a+a+{i}') for i in range(18)}
        rows = variants(texts)
        cache = BanReplay(HELPER, time.monotonic()+20)
        cache.extend(rows)
        self.assertEqual(cache.batches, 2)
        self.assertEqual(cache.banned(rows), c.p.banned(rows))
        for key, text in rows.items():
            self.assertEqual(cache.banned({key:text}), c.p.banned({key:text}))
        before = cache.receipt()
        cache.extend(rows)
        self.assertEqual(cache.receipt(), before)
        other = variants({'27': 'const solve=(x)=>x+1;'})
        cache.extend(other)
        self.assertEqual(cache.parsed_variants, 19)
        self.assertEqual(cache.banned({**rows, **other}), c.p.banned({**rows, **other}))

    def test_unrecorded_changed_hash_invalid_source_and_deadline_fail(self):
        cache = BanReplay(HELPER, time.monotonic()+10)
        rows = variants({'2':TEXT}); cache.extend(rows)
        key = next(iter(rows))
        with self.assertRaises(AssertionError): cache.banned({'unrecorded':TEXT})
        with self.assertRaises(AssertionError): cache.banned({key:TEXT+' '})
        with self.assertRaises(AssertionError): cache.extend({'2:bad':TEXT})
        with self.assertRaises(subprocess.CalledProcessError):
            cache.extend(variants({'3':'function solve('}))
        expired = BanReplay(HELPER, time.monotonic()-1)
        with self.assertRaises(TimeoutError): expired.extend(rows)
        self.assertEqual(expired.parsed_variants, 0)

    def test_full_replayed_trace_and_failure_prefix_match_scalar_parser(self):
        texts = {'10':TEXT, '2':TEXT.replace('(a)', '(b)').replace('a+a', 'b+b')}
        vocab = list(reversed(c.p.ALPHABET))+['aa','ab']
        menu = {'names':['aa','ab'], 'contexts':[
            {'pattern':['return ',None,'+',None,'']},
            {'pattern':['return ',None,'+',None,'']}]}
        got = engine.apply(texts,vocab,menu)
        dictionaries = {'own':vocab}
        baseline = report.replay_apply(got,texts,vocab,menu,dictionaries)
        cache = BanReplay(HELPER,time.monotonic()+20)
        cache.extend(got['ledger']['variants'])
        checked = report.replay_apply(got,texts,vocab,menu,dictionaries,ban_parser=cache.banned)
        self.assertEqual(baseline[0],checked[0])
        self.assertEqual(baseline[1].receipt(),checked[1].receipt())
        self.assertEqual(baseline[2],checked[2])
        self.assertEqual(report.global_union([('own',checked[1].receipt())],dictionaries,cache.banned),
                         report.global_union([('own',baseline[1].receipt())],dictionaries))
        # A cross-arm collision remains visible at the same encounter.
        original = report.Ledger(); batched = report.Ledger(ban_parser=cache.banned)
        bad = {'own':vocab,'other':vocab+[TEXT]}
        for ledger in (original,batched):
            with self.assertRaises(AssertionError): ledger.encounter({'10':TEXT},'collision',bad)
        self.assertEqual(original.receipt(),batched.receipt())
        corrupted = copy.deepcopy(got)
        corrupted['proposals'] += 1
        with self.assertRaises(AssertionError):
            report.replay_apply(corrupted,texts,vocab,menu,dictionaries,ban_parser=cache.banned)


if __name__ == '__main__':
    unittest.main()
