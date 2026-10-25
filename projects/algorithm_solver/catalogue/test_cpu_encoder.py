"""Source-free adapter checks; no encoder/model imports or execution."""
import unittest
from unittest.mock import patch

from .cpu_encoder import PinnedCPUEncoder


class CPUEncoderTests(unittest.TestCase):
    def construct(self, **changes):
        kwargs=dict(encoder_manifest='encoder',encoder_manifest_sha256='a'*64,
                    cpu_manifest='cpu',cpu_manifest_sha256='b'*64,native_python_sha256='c'*64)
        kwargs.update(changes)
        with patch('projects.algorithm_solver.catalogue.cpu_encoder.pinned',return_value={}):
            return PinnedCPUEncoder('/synthetic/model',**kwargs)

    def test_invalid_thread_and_batch_budgets_reject_before_loading(self):
        for threads in (0,3,4,True,'2'):
            with self.assertRaises(ValueError):self.construct(threads=threads)
        for size in (0,5,True):
            with self.assertRaises(ValueError):self.construct(batch_size=size)

    def test_text_validation_precedes_model_loading(self):
        encoder=self.construct()
        with patch.object(encoder,'_load',side_effect=AssertionError('must not load model')):
            for texts in ('text',[None],[''],['x'*16385],['x']*65):
                with self.assertRaises(ValueError):encoder.encode(texts)
            with self.assertRaises(ValueError):encoder.encode(['valid'],query=1)

    def test_query_instruction_does_not_modify_document_inputs(self):
        inputs=['Find a maximum.','Count letters.']
        documents=PinnedCPUEncoder.prepare_inputs(inputs)
        queries=PinnedCPUEncoder.prepare_inputs(inputs,query=True)
        self.assertEqual(documents,inputs)
        self.assertNotEqual(queries,inputs)
        self.assertTrue(all(q.endswith(d)for q,d in zip(queries,documents)))
        self.assertEqual(inputs,['Find a maximum.','Count letters.'])

    def test_actual_running_interpreter_is_bound_before_asset_reads(self):
        encoder=self.construct()
        with patch('projects.algorithm_solver.catalogue.cpu_encoder.sys.version_info',(3,13)), \
             patch('projects.algorithm_solver.catalogue.cpu_encoder.sys.executable','/different/python'), \
             patch('projects.algorithm_solver.catalogue.cpu_encoder.sha',side_effect=lambda p:'c'*64 if str(p)=='/usr/bin/python3' else 'd'*64):
            with self.assertRaisesRegex(ValueError,'running Python'):
                encoder._load()

    def test_truncation_is_explicit_not_semantic_verification(self):
        info=PinnedCPUEncoder.request_metadata(['a','b'],[1024,1025],True)
        self.assertEqual(info['truncated'],[False,True])
        self.assertEqual(info['modeled_token_counts'],[1024,1024])
        self.assertFalse(info['complete_query_semantics_verified'])
        with self.assertRaises(ValueError):PinnedCPUEncoder.request_metadata(['a'],[],False)

    def test_constructor_is_lazy_and_identity_is_not_recognition(self):
        encoder=self.construct(); identity=encoder.identity()
        self.assertFalse(identity['runtime_loaded_and_checked'])
        self.assertFalse(identity['recognition_qualified'])
        self.assertFalse(identity['old_calibration_reused'])
        self.assertEqual(len(identity['adapter_sha256']),64)


if __name__=='__main__':unittest.main()
