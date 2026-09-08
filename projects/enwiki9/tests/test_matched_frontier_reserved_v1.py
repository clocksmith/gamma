"""Synthetic comparator tests; no corpus or FX2 native process is executed."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import matched_frontier_reserved_v1 as gate


class Comparators(unittest.TestCase):
    def test_valid_mapping(self):
        value=gate.mapping(b'\x80\0\0\0\0'+b'\x07\0\0\0\0'+b'a'*10000,[97])
        self.assertTrue(value['supported'])
        self.assertEqual(value['out_of_alphabet_count'],0)

    def test_header_rejection(self):
        with self.assertRaises(ValueError): gate.mapping(b'bad',[97])

    def test_unsupported_alphabet(self):
        value=gate.mapping(b'\x80\0\0\0\0'+b'\x07\0\0\0\0'+b'a'*9999+b'b',[97])
        self.assertFalse(value['supported']); self.assertEqual(value['out_of_alphabet_count'],1)

    def test_unsupported_block(self):
        value=gate.mapping(b'\x80\0\0\0\0'+b'\x01\0\0\0\0'+b'a'*10000,[97])
        self.assertFalse(value['supported'])

    def test_short_mapping(self):
        self.assertFalse(gate.mapping(b'\x80\0\0\0\0',[])['supported'])

    def test_archive_header(self):
        storage=b'\x80\0\0\0\0'+b'\x07\0\0\0\0'+b'a'*10000
        vocab={'vocabulary_bitmap_hex':'00'*32}
        header=b'GFV1'+storage[5:10]+((1<<39)+10000).to_bytes(5,'big')+b'\0'*32
        gate.check_archive_header(header,storage,vocab)
        with self.assertRaises(ValueError): gate.check_archive_header(header[:9]+b'\0'+header[10:],storage,vocab)
        with self.assertRaises(ValueError): gate.check_archive_header(header[:-1],storage,vocab)

    def test_inventory_counts_model_and_aliases(self):
        model=dict(path='model',sha256='a'*64,bytes=100)
        alias=dict(model,path='source/model')
        counted,report=gate.inventory(dict(runtime_members=[model],source_members=[alias]),[])
        self.assertEqual(sum(n for _,n in counted),100)
        self.assertEqual(report['objects']['a'*64]['paths'],['model','source/model'])
        self.assertFalse(report['dependency_closure_complete'])
        with self.assertRaises(ValueError):gate.inventory(dict(runtime_members=[model],source_members=[dict(alias,bytes=99)]),[])

    def test_failure_classes(self):
        self.assertEqual(gate.failure_class(MemoryError()),'budget-exhausted')
        self.assertEqual(gate.failure_class(RuntimeError('encode exited 124')),'budget-exhausted')
        self.assertEqual(gate.failure_class(OSError()),'infrastructure-failure')
        self.assertEqual(gate.failure_class(ValueError()),'implementation-failure')

    def test_plain_actual_cli_inverse_and_repeat(self):
        parent=Path(os.environ['GAMMA_FRONTIER_UNIT_DIR'])
        with tempfile.TemporaryDirectory(dir=parent) as name:
            directory=Path(name); source=directory/'input';marker=directory/'phases.jsonl'
            raw=bytes(range(256))*8+b'<title>Same</title>\r\n<text>Same &amp; different\xff</text>'
            source.write_bytes(raw)
            row=gate.plain_arm(directory,'synthetic',source,marker)
            self.assertTrue(row['exact_inverse']);self.assertTrue(row['deterministic_repeat'])
            self.assertEqual(len(row['commands']),3)
            self.assertEqual((directory/'synthetic.raw').read_bytes(),raw)
            self.assertEqual(len(marker.read_text().splitlines()),6)

    def test_plain_failed_phase_rejected(self):
        with patch.object(gate.phase,'run_phase',return_value=dict(returncode=1,timeout=False,error=None)):
            with self.assertRaises(ValueError):gate.plain_arm(Path('.'),'fail',Path('absent'),Path('unused'))


if __name__=='__main__':unittest.main()
