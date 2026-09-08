"""Fixed Deflate ZIP source-cost diagnostic; synthetic input only, no prize credit."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from build_reproducible_source_zip import build_zip

SOURCES={
 'parent':('opcode_typed_anchor_bitmix_v1',{
  'p':'3e9c9ed25997ad10bac94575fb3da5009530ba04fa961da14a016fe89eec9a15',
  'program.py':'696c448c5cc29476b3a019fc64f13f23d8363f017b4d5821c5ed713c3bbf5b04'}),
 'observed':('opcode_field_confirmation1m_q0_v1',{
  'p':'3e9c9ed25997ad10bac94575fb3da5009530ba04fa961da14a016fe89eec9a15',
  'program.py':'72fb9daa43da614a378df586d6db8e456903dd6121a1845d90004897d3f9ebd7',
  'field_codec.py':'ba556b32e43dc3af3f9278da75b939b6fbe660c626530b3ecfef244d4bac936a'}),
 'compact':('opcode_field_compact_v1',{
  'p':'7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8',
  'program.py':'7361c8aa3695ec9d1556be02de66a1f0781414e78b44827511fb08bf8c8c05eb'})}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def record(path):return dict(path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=sha(path))

CHILD='''import importlib.util,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('codec',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
data=Path(sys.argv[3]).read_bytes();out=getattr(m,sys.argv[2])(data)
with Path(sys.argv[4]).open('xb') as f:f.write(out)
'''

def main():
 out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
 fixture=out/'fixture.raw'
 fixture.write_bytes((b'<title>Oakford</title><text xml:space="preserve">Oakford</text>\n').ljust(65,b' '))
 rows=[]
 for name,(cid,files) in SOURCES.items():
  source=ROOT/'programs'/cid
  for f,h in files.items():
   if sha(source/f)!=h:raise ValueError('source differs: '+str(source/f))
  z=out/(name+'.zip');repeat=out/(name+'.repeat.zip')
  build_zip(source,sorted(files),z,zipfile.ZIP_DEFLATED)
  build_zip(source,sorted(files),repeat,zipfile.ZIP_DEFLATED)
  if z.read_bytes()!=repeat.read_bytes():raise ValueError('source ZIP nondeterministic')
  extracted=out/(name+'-extracted');extracted.mkdir()
  with zipfile.ZipFile(z) as archive:
   if archive.namelist()!=sorted(files) or archive.testzip() is not None:raise ValueError('source ZIP invalid')
   for f,h in files.items():
    content=archive.read(f)
    if hashlib.sha256(content).hexdigest()!=h:raise ValueError('extracted source differs')
    with (extracted/f).open('xb') as stream:stream.write(content)
  commands=[]
  paths=[out/(name+x) for x in ('.arc','.raw','.repeat.arc')]
  for op,src,dst in [('compress',fixture,paths[0]),('decompress',paths[0],paths[1]),('compress',paths[1],paths[2])]:
   cmd=[sys.executable,'-c',CHILD,str(extracted/'program.py'),op,str(src),str(dst)]
   r=subprocess.run(cmd,capture_output=True,timeout=30)
   (out/(name+'-'+op+('-repeat' if dst==paths[2] else '')+'.stderr')).write_bytes(r.stderr)
   if r.returncode:raise ValueError('relocated codec failed: '+r.stderr.decode(errors='replace'))
   commands.append(cmd)
  if paths[1].read_bytes()!=fixture.read_bytes() or paths[0].read_bytes()!=paths[2].read_bytes():raise ValueError('relocated replay differs')
  rows.append(dict(name=name,candidate=cid,source_files=[record(source/f) for f in sorted(files)],
                   source_zip=record(z),repeat_zip=record(repeat),archive=record(paths[0]),restored=record(paths[1]),
                   repeat_archive=record(paths[2]),commands=commands,exact_inverse=True,deterministic_repeat=True,
                   required_local_source_bytes=sum((source/f).stat().st_size for f in files)))
 result=dict(schema='gamma.enwiki9.source-zip-diagnostic.v1',synthetic_only=True,corpus_executed=False,
             source_zip_method='ZIP_DEFLATED level9; deterministic direct entries via existing build_reproducible_source_zip.py',
             source_builder=record(ROOT/'tools/build_reproducible_source_zip.py'),reproducer=record(Path(__file__).resolve()),
             fixture=record(fixture),rows=rows,complete_package_bytes=None,objective_credit_bytes=0,
             limitations=['This is a local source-component inventory, not a ready submission.',
                          'CLI/build entry, options, license closure and runtime dependencies are excluded and unresolved.',
                          'Official source-package multiplicity depends on the selected packaging form.',
                          'Synthetic equality does not establish compact corpus parity.'])
 with (out/'receipt.json').open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
 print(json.dumps({r['name']:r['source_zip']['bytes'] for r in rows}))

if __name__=='__main__':main()
