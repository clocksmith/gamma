"""Canonical sort equivalence, bounded buffers, and complete observer parity."""
import hashlib
from pathlib import Path
import sys
import tempfile
import tracemalloc
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import opcode_terminal_bounded_sort_v1 as bounded
import opcode_field_repair_cli_v1 as old
import opcode_previous_word_bounded_observe_v1 as word
import opcode_previous_word_compact_observe_v1 as compact
from opcode_field_compact_observe_v1 import load

class BoundedAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'results')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.context=patch.object(bounded,'SCRATCH_ROOT',self.root)
        self.context.start();self.addCleanup(self.context.stop)

    def test_exact_bytes_multipass_segments_and_pristine_rows(self):
        table={key:[i,1] for i,key in enumerate([0,-1,1,256,65536,'s',b's',(1,2),(b'x',256),None,False])}
        for reverse in [False,True]:
            current=dict(reversed(list(table.items()))) if reverse else table
            for include in [lambda row:True,lambda row:row[0]%2]:
                expected=old.CountedHash(b'test');actual=old.CountedHash(b'test')
                old.table_hash(expected,('literal',11),current,tuple,include)
                with patch.multiple(bounded,CHUNK_RECORDS=2,FAN_IN=2,SEGMENT_BYTES=25):
                    bounded.table_hash(actual,('literal',11),current,tuple,include)
                self.assertEqual((expected.hexdigest(),expected.bytes),(actual.hexdigest(),actual.bytes))
                self.assertEqual(list(self.root.iterdir()),[])

    def test_empty_and_failure_cleanup(self):
        h=hashlib.sha256();bounded.table_hash(h,'empty',{})
        with self.assertRaises(RuntimeError):
            bounded.table_hash(h,'broken',{i:i for i in range(100)},lambda value:(_ for _ in ()).throw(RuntimeError()))
        self.assertEqual(list(self.root.iterdir()),[])

    def test_auxiliary_memory_is_bounded(self):
        table={(i,i%97):[1,2] for i in range(80000)}
        tracemalloc.start()
        h=hashlib.sha256();bounded.table_hash(h,'fixture',table,tuple)
        _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        self.assertLess(peak,4*1024**2)
        reference=hashlib.sha256();old.table_hash(reference,'fixture',table,tuple)
        self.assertEqual(h.digest(),reference.digest())
        print('bounded_sort_peak_auxiliary_bytes='+str(peak))

    def test_full_archive_and_audit_parity_all_arms(self):
        root=Path(__file__).resolve().parents[1]
        module=load(root/'programs/opcode_previous_word_confirmation1m_q0_v1/program.py')
        raw=b'<title>Oak</title>First Elm First Elm\xff\n'*8
        for arm in 'PKDS':
            archive,expected=compact.execute(module,'encode',raw,arm)
            actual,audit=word.execute(module,'encode',raw,arm)
            self.assertEqual(actual,archive);self.assertEqual(audit,expected)
            restored,decode=word.execute(module,'decode',archive,arm)
            self.assertEqual(restored,raw);self.assertEqual(decode,expected)

if __name__=='__main__':unittest.main()
