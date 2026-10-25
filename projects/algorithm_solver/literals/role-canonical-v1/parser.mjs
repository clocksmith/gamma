// Explicit immutable upstream-source loader; no generated dist or lifecycle code.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
export const parserRoot=path.resolve(process.env.GAMMA_PARSER_ROOT||'/workspace/shared/gamma-parser-source');
export const receiptSha256='dd550ff8cb1966e56c0b2fc4a56e376d4f71ceb3175222300eb6ccfc71766365';
const hash=(kind,raw)=>crypto.createHash(kind).update(raw).digest('hex');
const raw=fs.readFileSync(path.join(parserRoot,'receipt.json'));
if(hash('sha256',raw)!==receiptSha256)throw Error('parser receipt identity drift');
const receipt=JSON.parse(raw);
if(!receipt.all_git_blob_ids_verified||!receipt.no_source_bytes_modified||receipt.upstream_files.length!==46)throw Error('invalid parser receipt');
for(const row of receipt.upstream_files){
 const originalRoot='/workspace/shared/gamma-parser-source/';
 if(!row.local.startsWith(originalRoot))throw Error('parser source path outside receipt root');
 const file=path.resolve(parserRoot,row.local.slice(originalRoot.length));
 if(!file.startsWith(parserRoot+path.sep))throw Error('parser path escape');
 const bytes=fs.readFileSync(file);
 if(bytes.length!==row.bytes||hash('sha256',bytes)!==row.sha256||hash('sha1',Buffer.concat([Buffer.from(`blob ${bytes.length}\0`),bytes]))!==row.git_sha)throw Error('parser source identity drift');
}
const load=entry=>import(pathToFileURL(path.join(parserRoot,'node_modules',entry)).href);
export const acorn=await load('acorn/src/index.js');
export const scope=await load('eslint-scope/lib/index.js');
export const astring=await load('astring/src/astring.js');
