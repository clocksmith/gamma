import test from 'node:test';import assert from 'node:assert/strict';
import {FAMILIES,TASK_SPLIT,TASK_SPEC_SHA256,buildDispatchCheck,buildTaskPopulation,writeTaskPopulation} from './tasks.mjs';
// This only exercises mechanics with a fixture seed and a stand-in prompt
// serializer. The experiment must use the existing buildWgslWriterPrompt.
const build=()=>buildTaskPopulation({seed:123,buildPrompt:task=>JSON.stringify({specification:task.specification,interfaceContract:task.interfaceContract})});
const f32=(buffer)=>{const b=Uint8Array.from(buffer),v=new DataView(b.buffer);return Array.from({length:b.length/4},(_,i)=>v.getFloat32(i*4,true));};
test('semantic families and expression components are disjoint; output projections keep oracles private',()=>{
 const p=build();assert.deepEqual(p.manifest.counts,{smoke:2,selection:4,confirmation:16});
 assert.equal(new Set(Object.values(TASK_SPLIT).flat()).size,22);assert.equal(new Set(p.rows.map(r=>r.expressionSha256)).size,22);
 for(const row of p.rows){assert.equal(row.referenceShader,undefined);assert.equal(row.expected,undefined);assert.equal(row.visibleChecks.length,1);assert.equal(row.visibleChecks[0].expected,undefined);assert.equal(p.checks[row.taskId].confirmation.length,12);}
 assert.deepEqual(build().manifest,p.manifest);assert.match(TASK_SPEC_SHA256,/^[a-f0-9]{64}$/);
 assert.throws(()=>buildTaskPopulation({seed:123,buildPrompt:()=>'',excludedFamilyIds:[FAMILIES[0].id]}),/Exposed/);
 assert.throws(()=>buildTaskPopulation({seed:123,buildPrompt:task=>task.specification,exposedReferenceHashes:[p.references[p.rows[0].taskId].sha256]}),/Exposed/);
});
test('CPU oracles agree with independently specified examples',()=>{
 const expected={sign_bit:1,tent:.75,cubic:.015625,softsign:.2,gated_difference:1.75,rms_pair:Math.sqrt(2.03125),discriminant:-7.9375,signed_root:.5,inverse_magnitude:1,smoothstep_unit:.15625,positive_modulus:.25,round_to_grid:0,minimum_magnitude:.25,log_magnitude:Math.log(1.25),exponential_decay:Math.exp(-.25),bounded_product:1/3.25,signed_angle:Math.atan2(2,.25),transfer_sign:2,periodic_triangle:.5,huber_loss:.03125,quadratic_blend:-.75,window_select:2};
 for(const family of FAMILIES){const id=family.id.slice(5),actual=family.oracle(.25,2,.75,2.5);assert.ok(Math.abs(actual-expected[id])<=1e-6,`${id}: ${actual} != ${expected[id]}`);}
 const family=FAMILIES.find(f=>f.id==='gain-positive_modulus');assert.equal(family.oracle(-.25,0,.75,2.5),.5);
});
test('prepared checks retain canaries, readback inputs, overdispatch, and exact input permutation',()=>{
 const family=FAMILIES.find(f=>f.id==='gain-cubic'),args={seed:7,length:33,workgroupSize:32};
 const base=buildDispatchCheck(family,args),reversed=buildDispatchCheck(family,{...args,permuted:true});
 assert.deepEqual(base.request.dispatch,[2,1,1]);assert.deepEqual(reversed.expected,[...base.expected].reverse());
 assert.deepEqual(f32(reversed.request.buffers[0].bytes),f32(base.request.buffers[0].bytes).reverse());
 assert.ok(f32(base.request.buffers[2].bytes).every(v=>v===base.output.canary));assert.equal(base.output.offset,16);assert.ok(base.output.totalElements>16+33+16);
 assert.equal(base.request.code,undefined,'candidate source must be attached only at execution');
 assert.ok(base.request.buffers.slice(0,3).every(b=>b.readback));
});
test('writing fails before any filesystem operation without the matching freeze',async()=>{
 await assert.rejects(writeTaskPopulation(build(),'/not-written',{freezeSha256:'bad',frozenTaskSpecSha256:TASK_SPEC_SHA256}),/frozen/);
 await assert.rejects(writeTaskPopulation(build(),'/not-written',{freezeSha256:'a'.repeat(64),frozenTaskSpecSha256:'b'.repeat(64)}),/frozen/);
});

test('exposure registry covers actual frozen oracle branches with semantic witnesses',async()=>{
 const {auditExposedFamilies}=await import('./exposure_audit.mjs');
 const {readFile}=await import('node:fs/promises');
 const stored=JSON.parse(await readFile(new URL('./exposure-registry.json',import.meta.url),'utf8'));
 assert.deepEqual(auditExposedFamilies(),stored);
 assert.deepEqual(stored.summary,{exposedFamilies:24,newFamilies:22,exposedComparisons:528,newPairComparisons:231});
 assert.equal(stored.confirmationEvaluated,false);
});

test('real frozen writer prompt imports through an isolated namespace without touching shared namespace',async()=>{
 const {mkdtemp,mkdir,copyFile,symlink,writeFile,rm}=await import('node:fs/promises');
 const {tmpdir}=await import('node:os');const {join,resolve,dirname}=await import('node:path');const {fileURLToPath,pathToFileURL}=await import('node:url');
 const gamma=resolve(dirname(fileURLToPath(import.meta.url)),'../../../..'),campaign=join(gamma,'projects/distillation/wgsl/campaign'),doppler=resolve(process.env.DOPPLER_ROOT||join(gamma,'../doppler'));
 const namespaceRoot=await mkdtemp(join(tmpdir(),'gamma-channel-gain-prompt-fixture-'));
 try{
  await mkdir(join(namespaceRoot,'tools/lib'),{recursive:true});await mkdir(join(namespaceRoot,'src/tooling'),{recursive:true});
  await writeFile(join(namespaceRoot,'package.json'),JSON.stringify({type:'module'}));
  for(const relative of ['tools/lib/wgsl-writer-semantic-harness.js','tools/lib/wgsl-semantic-harness.js','src/tooling/wgsl-repair-semantic-gate.js'])await copyFile(join(campaign,relative),join(namespaceRoot,relative));
  await symlink(join(doppler,'src/formats'),join(namespaceRoot,'src/formats'));await symlink(join(doppler,'src/experimental'),join(namespaceRoot,'src/experimental'));
  const {buildWgslWriterPrompt}=await import(pathToFileURL(join(namespaceRoot,'tools/lib/wgsl-writer-semantic-harness.js')).href);
  const prompt=buildWgslWriterPrompt({taskId:'mechanics-fixture-only',specification:'Fixture specification.',interfaceContract:{entryPoint:'main'}},{responseContract:'complete_wgsl_compute_shader_only_v1'});
  assert.ok(prompt.includes('<specification>\nFixture specification.\n</specification>'));assert.ok(prompt.startsWith('Author one complete WGSL compute shader'));
 }finally{await rm(namespaceRoot,{recursive:true,force:true});}
});
