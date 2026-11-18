import test from 'node:test';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { scaleCompiledStopChannel } from './stop_channel_control.mjs';
const modulePath = process.env.FASTWEIGHT_MODULE;
test('actual v4 compiler: intervention changes only stop contribution', {
  skip: !modulePath && 'Set FASTWEIGHT_MODULE to the unchanged v4 compiler',
}, async () => {
  const { compileClosedFormLayerLoRA } = await import(pathToFileURL(modulePath));
  const dHidden = 3, dInter = 5;
  const lines = Array.from({ length: 4 }, (_, i) => [10+i,20+i,30+i,40+i,50+i,99,70+i,0]);
  const supportIds = lines.flat();
  const features = (n, seed) => Float32Array.from({length:n*dInter},
    (_,j) => Math.sin((j+1)*(seed+1)*0.31)+0.1);
  const isoEntries = lines.map((lineIds,i) => ({
    lineIds, relAnchor:5, hFlat:new Float32Array(lineIds.length*dHidden).fill(1),
    layerZMap:new Map([[1,features(lineIds.length,i)]]), bareTop:[2],
  }));
  const compiled = compileClosedFormLayerLoRA({
    supportIds, headerIds:[], nlId:0, dHidden,dInter,targetLayers:[1],
    isoEntries, catEntry:{layerZMap:new Map([[1,features(supportIds.length,7)]])},
    finalNormG:new Float32Array(dHidden).fill(1),
    getLmRow:tid=>Float32Array.from({length:dHidden},(_,j)=>Math.sin(tid+j+1)),
  });
  assert.equal(compiled.active,true);
  assert.equal(compiled.anchorsCount,4);
  const identity = scaleCompiledStopChannel(compiled,1);
  assert.deepEqual(identity,compiled);
  const removed = scaleCompiledStopChannel(compiled,0);
  const before = compiled.layers.get(1), after = removed.layers.get(1);
  const z = [0.1,0.2,-0.3,0.4,-0.5];
  const rank = compiled.rank;
  const channels = Array.from({length:rank},(_,r)=>
    z.reduce((v,x,k)=>v+x*before.a[k*rank+r],0));
  const project = b=>Array.from({length:dHidden},(_,j)=>
    channels.reduce((v,x,r)=>v+x*b[r*dHidden+j],0));
  const full=project(before.b), noStop=project(after.b);
  for(let j=0;j<dHidden;j++){
    assert.ok(Number.isFinite(full[j]));
    const expected=channels[rank-1]*before.b[(rank-1)*dHidden+j];
    assert.ok(Math.abs((full[j]-noStop[j])-expected)<1e-10);
  }
  assert.ok(before.b.slice((rank-1)*dHidden).some(v=>v!==0));
});
