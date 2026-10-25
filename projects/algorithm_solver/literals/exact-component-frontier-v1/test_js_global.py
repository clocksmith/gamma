"""Public synthetic metadata-binding tests; never load a real pool/case."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import run_js_global as g


class GlobalMetadataControls(unittest.TestCase):
    def test_pinned_reader_rejects_changed_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'metadata.json';raw=b'{"sources": []}\n';p.write_bytes(raw)
            sha=hashlib.sha256(raw).hexdigest()
            self.assertEqual(g.pinned(p,sha),{'sources':[]})
            p.write_bytes(raw+b' ')
            with self.assertRaises(ValueError):g.pinned(p,sha)

    def test_ledger_canonical_hash_does_not_accept_newline_freeze_hash(self):
        value={'b':2,'a':1}
        canonical=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
        self.assertEqual(g.digest(value),hashlib.sha256(canonical).hexdigest())
        self.assertNotEqual(g.digest(value),hashlib.sha256(canonical+b'\n').hexdigest())


if __name__=='__main__':unittest.main()
