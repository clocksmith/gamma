"""Synthetic source-binding and native call-order tests; no codec process."""
import copy
import hashlib
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import fx2_xml_word_native_adapter_v1 as adapter


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=adapter.build(); cls.source={}
        for row in cls.manifest['files']:
            text=(adapter.PARENT/row['source_path']).read_text()
            for change in row['replacements']:
                assert text.count(change['before'])==1
                text=text.replace(change['before'],change['after'])
            assert hashlib.sha256(text.encode()).hexdigest()==row['patched_sha256']
            cls.source[row['source_path']]=text

    def test_deterministic_adapter_and_added_bindings(self):
        self.assertEqual(self.manifest,adapter.build())
        for row in self.manifest['added_files']:
            raw=(adapter.ROOT/row['source']['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),row['source']['sha256'])

    def test_only_one_indirect_context_reference_changes(self):
        text=self.source['src/predictor.cpp']
        self.assertEqual(text.count('nonstationary_, gamma_context,'),1)
        self.assertIn("gamma_xml_arm_ != 'P' && params.size() == 1 && params[0] == 0",text)
        self.assertEqual(text.count('const Context& context = manager_.AddSparseContext(manager_.words_, params);'),2)
        self.assertNotIn('std::srand',text)

    def test_pretrain_and_live_context_order(self):
        text=self.source['src/predictor.cpp']
        for method in ('Perceive','Pretrain'):
            body=text.split('void Predictor::'+method+'(int bit) {')[1]
            update=body.index('manager_.UpdateContexts(bit);')
            observe=body.index('GammaXmlUpdate(byte_update);')
            byteupdate=body.index('indirect_ns_models_[i].ByteUpdate();')
            self.assertLess(update,observe); self.assertLess(observe,byteupdate)
        body=text.split('void Predictor::GammaXmlUpdate(bool byte_update) {')[1]
        self.assertLess(body.index('gamma_xml_context_ = manager_.words_[0];'),
                        body.index('if (!gamma_xml_active_) return;'))

    def test_initialization_after_pretraining_and_finish_after_coding(self):
        text=self.source['src/runner.cpp']
        for boundary,end in [('Compress(temp_bytes','temp_in.close();'),
                             ('Decompress(*output_bytes','data_in.close();')]:
            position=text.index('  '+boundary)
            previous=text[:position]
            self.assertGreater(previous.rfind('p.GammaXmlBegin('),previous.rfind('preprocessor::Pretrain('))
            following=text[position:]
            self.assertLess(following.index('p.GammaXmlEnd();'),following.index(end))
        self.assertIn('GammaXmlBegin(dictionary, gamma_literal_header, *input_bytes)',text)
        self.assertIn('GammaXmlBegin(dictionary, gamma_literal_header, 0)',text)

    def test_dictionary_read_cannot_move_parent_cursor(self):
        body=adapter.METHODS.split('void Predictor::GammaXmlUpdate')[0]
        self.assertIn('pread(',body)
        for forbidden in ('fseek(', 'getc(', 'fread(', 'dup('): self.assertNotIn(forbidden,body)

    def test_coder_adapter_preserves_predict_and_perceive_calls(self):
        for file in ('src/coder/encoder.cpp','src/coder/decoder.cpp'):
            original=(adapter.PARENT/file).read_text(); patched=self.source[file]
            for call in ('p_->Predict()', 'p_->Perceive(bit)'):
                self.assertEqual(original.count(call),patched.count(call))
            self.assertNotIn('GammaFinalProbability',patched)


if __name__=='__main__': unittest.main()
