import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from projects.enwiki9.lib.native_trace_cache_v1 import release_closed_file,memory_snapshot


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)

    def test_real_release_preserves_bytes_and_metadata(self):
        p=self.root/'trace';raw=bytes(range(256))*4096;p.write_bytes(raw);before=p.stat()
        r=release_closed_file(p)
        self.assertEqual(p.read_bytes(),raw);self.assertEqual(p.stat().st_mtime_ns,before.st_mtime_ns)
        self.assertEqual(r['bytes'],len(raw));self.assertTrue(r['flushed'])

    def test_symlinks_rejected(self):
        target=self.root/'target';target.write_bytes(b'exact');p=self.root/'link';p.symlink_to(target)
        with self.assertRaises(OSError):release_closed_file(p)
        self.assertEqual(target.read_bytes(),b'exact')

    def test_flush_precedes_advice_and_failure_is_not_silenced(self):
        p=self.root/'trace';p.write_bytes(b'exact');calls=[]
        with patch('os.fdatasync',side_effect=lambda fd:calls.append('sync')),patch('os.posix_fadvise',side_effect=lambda *args:calls.append('advice')):
            release_closed_file(p)
        self.assertEqual(calls,['sync','advice'])
        with patch('os.posix_fadvise',side_effect=OSError('unavailable')):
            with self.assertRaises(OSError):release_closed_file(p)

    def test_missing_optional_memory_fields_are_explicit(self):
        self.assertTrue(memory_snapshot(self.root)['missing_diagnostics'])
        (self.root/'memory.current').write_text('100');(self.root/'memory.stat').write_text('anon 40\nfile 60\n')
        self.assertEqual(memory_snapshot(self.root),dict(current_bytes=100,anon_bytes=40,file_bytes=60,missing_diagnostics=[]))


if __name__=='__main__':unittest.main()
