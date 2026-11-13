// Read-only, bounded-memory converted-shard integrity check; no GPU imports.
import {readFile,writeFile,stat} from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import {createHash} from 'node:crypto';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
const [modelRoot,runtimeRoot,output]=process.argv.slice(2);
if(!modelRoot||!runtimeRoot||!output)throw Error('Usage: node verify_converted_model.mjs MODEL_ROOT DOPPLER_ROOT OUTPUT_JSON');
const sha=x=>createHash('sha256').update(x).digest('hex');
const manifestBytes=await readFile(join(modelRoot,'manifest.json')),manifest=JSON.parse(manifestBytes);
const {validateManifest}=await import(pathToFileURL(resolve(runtimeRoot,'src/formats/rdrr/validation.js')));
const {createHasher}=await import(pathToFileURL(resolve(runtimeRoot,'src/storage/blake3.js')));
const validation=validateManifest(manifest);if(!validation.valid)throw Error(JSON.stringify(validation));
if(manifest.hashAlgorithm!=='blake3')throw Error('This pinned artifact must retain blake3 shard identity');
const started=performance.now(),shards=[];let bytesRead=0;
for(const shard of manifest.shards){
 const filename=join(modelRoot,shard.filename);if((await stat(filename)).size!==shard.size)throw Error(`Shard size mismatch: ${shard.index}`);
 const begin=performance.now(),h=createHasher();let size=0;
 for await(const chunk of createReadStream(filename,{highWaterMark:4*1024*1024})){h.update(chunk);size+=chunk.byteLength;}
 const actual=Buffer.from(await h.finalize()).toString('hex');
 if(actual!==shard.hash)throw Error(`Shard hash mismatch: ${shard.index}`);
 shards.push({index:shard.index,filename:shard.filename,bytes:size,expected:shard.hash,actual,passed:true,elapsedMs:performance.now()-begin});bytesRead+=size;
 if(shards.length%25===0||shards.length===manifest.shards.length)console.log(JSON.stringify({checked:shards.length,total:manifest.shards.length,bytesRead,elapsedMs:performance.now()-started}));
}
if(bytesRead!==manifest.totalSize)throw Error('Manifest totalSize differs from checked shard bytes');
if(sha(await readFile(join(modelRoot,'manifest.json')))!==sha(manifestBytes))throw Error('Manifest changed during verification');
const receipt={schema:'gamma.channel-gain-converted-shard-integrity/v1',observedAt:new Date().toISOString(),modelId:manifest.modelId,manifestSha256:sha(manifestBytes),artifactIdentity:manifest.artifactIdentity,manifestValidation:validation,shardHashAlgorithm:'blake3',hashImplementationSha256:sha(await readFile(join(runtimeRoot,'src/storage/blake3.js'))),shards,bytesRead,elapsedMs:performance.now()-started,passed:true,gpuExecuted:false,inferenceExecuted:false};
await writeFile(output,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({passed:true,output,shards:shards.length,elapsedMs:receipt.elapsedMs}));
