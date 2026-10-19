"""Training input/idempotence checks on synthetic fixtures; no fitting run."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from algsolve.synth.train_typed_suby import training_view, train
from algsolve.rebuild_recognition import sha


class ProposedTrainingBoundaries(unittest.TestCase):
    def test_only_fit_targets_form_labels_and_alternatives_share_loss_group(self):
        def pair(uid,split,target):return {'uid':uid,'problem_family':uid,'learning_split':split,
                                        'input':{'statement':uid},'target':target}
        pairs=[pair('first','development_fit',1),pair('audit','development_audit',object()),
               pair('first','development_fit',2),pair('second','development_fit',3)]
        fit,requests,indices,groups=training_view(pairs)
        self.assertEqual([p['target'] for p in fit],[1,2,3])
        self.assertEqual(indices,[0,0,2]);self.assertEqual(groups,[[0,1],[2]])
        self.assertTrue(all('target' not in r for r in requests))

    def test_completed_training_resumes_without_importing_model_or_fitting(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'model.pt').write_bytes(b'synthetic fixture')
            h=sha(root/'model.pt');(root/'summary.json').write_text(json.dumps({'checkpoint_sha256':h,'artifacts_sha256':{'model.pt':h}}))
            with patch('algsolve.synth.train_typed_suby.OUTPUT',root),patch('algsolve.synth.train_typed_suby.freeze',return_value=(None,)*7),contextlib.redirect_stdout(io.StringIO()):
                train(None)
            (root/'model.pt').write_bytes(b'drift')
            with patch('algsolve.synth.train_typed_suby.OUTPUT',root),patch('algsolve.synth.train_typed_suby.freeze',return_value=(None,)*7):
                with self.assertRaises(ValueError):train(None)

    def test_partial_training_never_silently_restarts(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'training-started.json').write_text('{}')
            with patch('algsolve.synth.train_typed_suby.OUTPUT',root),patch('algsolve.synth.train_typed_suby.freeze',return_value=(None,)*7):
                with self.assertRaisesRegex(ValueError,'Interrupted training'):train(None)

if __name__=='__main__':unittest.main()
