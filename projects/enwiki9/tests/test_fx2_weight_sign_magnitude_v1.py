"""Independent synthetic inverses and complete pre-weight state agreement."""
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import fx2_weight_marginal_fixtures_v1 as reference
import fx2_weight_sign_magnitude_v1 as adapter


class SignMagnitudeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.environ['FX2_SIGN_TMP'])
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.probe=os.environ['FX2_SIGN_PROBE']
        self.parent=os.environ['FX2_SIGN_PARENT']

    def command(self,binary,mode,source,target,trace=None,success=True):
        args=[binary,mode,str(source),str(target)]
        if trace is not None:args.append(str(trace))
        child=subprocess.run(args,capture_output=True,timeout=30)
        self.assertEqual(child.returncode==0,success,child.stderr.decode())

    def compare(self,tensors):
        original=self.root/'original';original.write_bytes(reference.encode_reference(tensors))
        for arm in ('P','K','D'):
            archive,restored,repeat=[self.root/(arm+s) for s in ('.arc','.raw','.repeat')]
            self.command(self.probe,arm,original,archive,self.root/'encode.trace' if arm=='D' else None)
            self.command(self.probe,'restore',archive,restored,self.root/'decode.trace' if arm=='D' else None)
            self.command(self.probe,arm,original,repeat)
            self.assertEqual(original.read_bytes(),restored.read_bytes())
            self.assertEqual(archive.read_bytes(),repeat.read_bytes())
        self.command(self.parent,'D',original,self.root/'parent.arc')
        self.assertEqual((self.root/'P.arc').read_bytes(),(self.root/'parent.arc').read_bytes())
        self.assertEqual((self.root/'P.arc').read_bytes(),(self.root/'K.arc').read_bytes())
        self.assertEqual((self.root/'encode.trace').read_bytes(),(self.root/'decode.trace').read_bytes())
        rows=list(struct.iter_unpack('<12IB',(self.root/'encode.trace').read_bytes()))
        print(json.dumps(dict(test=self.id(),P=(self.root/'P.arc').stat().st_size,
                              D=(self.root/'D.arc').stat().st_size,state_boundaries=len(rows))))
        return rows

    def check_states(self,rows,sequences):
        position=0
        for sequence in sequences:
            magnitude=[1]+[2]*7;sign=[1,1]
            for q in sequence:
                row=rows[position];position+=1
                self.assertEqual(row,tuple(magnitude+sign+[sum(magnitude),sum(sign),q+7]))
                m=abs(q);magnitude[m]+=1
                if sum(magnitude)>=65536:magnitude=[(v+1)//2 for v in magnitude]
                if m:
                    sign[int(q<0)]+=1
                    if sum(sign)>=65536:sign=[(v+1)//2 for v in sign]
        self.assertEqual(position,len(rows))

    def test_all_encodings(self):
        values=list(range(-7,8))
        rows=self.compare([reference.tensor('int4',0,[15],1,values),
                           reference.tensor('raw',0,[4],0,[0,255,128,10]),
                           reference.tensor('bf16',1,[2],2,[255,255,0,128]),
                           reference.tensor('f32',2,[2],3,[255,255,255,127,0,0,0,128]),
                           reference.tensor('empty',0,[0,3],1,[])])
        self.check_states(rows,[values,[]])

    def test_empty_document(self):self.assertEqual(self.compare([]),[])

    def test_zero_omits_sign_updates(self):
        values=[0]*70000
        rows=self.compare([reference.tensor('zero',0,[len(values)],1,values)])
        self.check_states(rows,[values])
        self.assertTrue(all(row[8:10]==(1,1) for row in rows))

    def test_independent_signs(self):
        rng=random.Random(9461)
        values=[rng.randrange(1,8)*(-1 if rng.randrange(4)==0 else 1) for _ in range(30000)]
        self.check_states(self.compare([reference.tensor('independent',0,[len(values)],1,values)]),[values])

    def test_magnitude_dependent_signs(self):
        rng=random.Random(9461)
        values=[rng.randrange(1,8) for _ in range(30000)]
        values=[-v if v%2 else v for v in values]
        self.check_states(self.compare([reference.tensor('dependent',0,[len(values)],1,values)]),[values])
        self.assertGreater((self.root/'D.arc').stat().st_size,(self.root/'P.arc').stat().st_size)

    def test_rescale_and_tensor_reset(self):
        sequences=[[-7]*70000,[7]*10,[0,-1,2,-3,4,-5,6,-7]]
        rows=self.compare([reference.tensor(str(i),0,[len(v)],1,v) for i,v in enumerate(sequences)])
        self.check_states(rows,sequences)

    def test_corruption_and_exclusive_output(self):
        self.compare([reference.tensor('a',0,[3],1,[-7,0,7])])
        archive=self.root/'D.arc';sealed=archive.read_bytes()
        self.command(self.probe,'D',self.root/'original',archive,success=False)
        self.assertEqual(archive.read_bytes(),sealed)
        for i,data in enumerate((sealed[:-1],sealed+b'\0',b'BROKEN!!'+sealed[8:],sealed[:8]+b'\xff'*4+sealed[12:])):
            source=self.root/f'bad{i}';source.write_bytes(data);target=self.root/f'restore{i}'
            self.command(self.probe,'restore',source,target,success=False)
            self.assertFalse(target.exists())

    def test_adapter_authentication_and_output_preservation(self):
        with self.assertRaisesRegex(ValueError,'sealed adaptive parent'):
            adapter.render(adapter.PARENT.read_bytes()+b'\n')
        path=self.root/'header';adapter.materialize(path);sealed=path.read_bytes()
        with self.assertRaises(FileExistsError):adapter.materialize(path)
        self.assertEqual(path.read_bytes(),sealed)


if __name__=='__main__':unittest.main()
