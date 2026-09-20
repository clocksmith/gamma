"""Real envelope execution with a synthetic identity codec, never score evidence."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from gamma_enwiki9.packaging.fx2_envelope import assemble

@unittest.skipUnless(shutil.which('g++'), 'C++ compiler required')
class EnvelopeTests(unittest.TestCase):
    def test_inverse_publication_and_footer(self):
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary);source=Path(__file__).parents[1]/'src/gamma_enwiki9/packaging/fx2_envelope.cpp'
            subprocess.run(['g++','-std=c++17','-Os',str(source),'-o',str(p/'wrapper')],check=True,timeout=60)
            (p/'codec').write_text('#!/bin/sh\ncp "$3" "$4"\n')
            (p/'dict').write_bytes(b'dictionary');(p/'weights').write_bytes(b'weights')
            (p/'input').write_bytes(bytes(range(256))*3)
            assemble(p/'wrapper',p/'codec',p/'dict',p/'weights',p/'comp9')
            subprocess.run([str(p/'comp9'),'input'],cwd=p,check=True,timeout=10)
            subprocess.run([str(p/'archive9')],cwd=p,check=True,timeout=10)
            self.assertEqual((p/'enwik9').read_bytes(),(p/'input').read_bytes())
            self.assertNotEqual(subprocess.run([str(p/'archive9')],cwd=p,stderr=subprocess.PIPE).returncode,0)
            (p/'enwik9').unlink()
            (p/'bad').write_bytes((p/'archive9').read_bytes()[:-1]);(p/'bad').chmod(0o755)
            self.assertNotEqual(subprocess.run([str(p/'bad')],cwd=p,stderr=subprocess.PIPE).returncode,0)
            self.assertFalse((p/'enwik9').exists())
            self.assertFalse(list(p.glob('.gamma-fx2-*')))
