// Trusted parser only: exact8 inert sources; no transformation or evaluation.
import './controls-v2.mjs';
import fs from 'node:fs';import crypto from 'node:crypto';import {extremaSubset}from './alignment-v2.mjs';
const packet=JSON.parse(fs.readFileSync(0,'utf8'));const expected=['1014','1121','123','1375','1725','1732','2873','55'];
if(packet.variants.length!==8||JSON.stringify(packet.variants.map(v=>v.problem_id).sort())!==JSON.stringify(expected))throw Error('exact8 scope');
let bytes=0;for(const v of packet.variants){if(crypto.createHash('sha256').update(v.source).digest('hex')!==v.source_sha256)throw Error('exact source hash');bytes+=Buffer.byteLength(v.source);console.log(JSON.stringify({key:v.key,source_sha256:v.source_sha256,source_bytes:Buffer.byteLength(v.source),...extremaSubset(v.source)}));}
if(bytes!==1053)throw Error('fixed source mass');console.log(JSON.stringify({done:8,source_bytes:bytes,candidate_execution:false,transformed_sources:0,qualification:false}));
