"""Exercise the actual driver on synthetic250KB and inherited mismatch checks."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zlib
import test_fx2_ratio_coder_gate_v1 as previous
from projects.enwiki9.tools import fx2_ratio_coder_opening250k_q0_v1 as gate


class CorpusTraceTests(previous.GateTests):
    def setUp(self):
        super().setUp()
        change=patch.object(previous,'gate',gate);change.start();self.addCleanup(change.stop)


class DriverScopeTests(unittest.TestCase):
    def test_cache_release_precedes_native_execution(self):
        obj=object.__new__(gate.NativeGate);events=[]
        with patch.object(obj,'release_observations',side_effect=lambda label:events.append(label)),patch.object(gate.TraceCacheGate,'run',side_effect=lambda *args:events.append('native')):
            obj.run('P-plain',['cmix'],120)
        self.assertEqual(events,['before-P-plain','native'])

    def test_manifest_hash_releases_only_owned_trace_pages(self):
        obj=object.__new__(gate.NativeGate);obj.result=Path('/owned')
        with patch.object(gate.TraceCacheGate,'artifact',return_value={'hash':'already-computed'}),patch.object(gate,'release_closed_file') as release:
            self.assertEqual(obj.artifact(Path('/owned/P-encode.ratio')),{'hash':'already-computed'})
            obj.artifact(Path('/external/P-encode.ratio'));obj.artifact(Path('/owned/archive.bin'))
            release.assert_called_once_with(Path('/owned/P-encode.ratio'))

    def test_actual_driver_consumes_full_population_and_retains_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            class FakeGate:
                result=Path(directory)
                work=Path(directory)/'work'
                def write(self,name,value):
                    (self.result/name).write_text(json.dumps(value))
            g=FakeGate();g.work.mkdir()
            raw=(bytes(range(256))*977)[:250000];(g.work/'population.raw').write_bytes(raw)
            class SyntheticCodec:
                def __init__(self,g,arm):self.g,self.arm,self.calls=g,arm,0
                def compress(self,raw):
                    phase='encode' if self.calls==0 else 'repeat';self.calls+=1
                    payload=zlib.compress(raw);(self.g.work/(self.arm+'-'+phase+'.cmix')).write_bytes(payload)
                    return payload
                def decompress(self,payload):
                    raw=zlib.decompress(payload);(self.g.work/(self.arm+'-decode.raw')).write_bytes(raw);return raw
            with patch.object(gate,'Codec',SyntheticCodec):
                result=gate.run_native_arm(g,'D',[],{'counted_files':[]})
            self.assertEqual(result['data_size'],250000)
            self.assertTrue(result['roundtrip_ok']);self.assertTrue(result['determinism']['single_host_byte_equal'])
            self.assertEqual((g.result/'D/restored.bin').read_bytes(),raw)
            self.assertEqual((g.result/'D/archive.bin').read_bytes(),(g.result/'D/repeat.bin').read_bytes())


if __name__=='__main__':unittest.main()
