// Run before corpus materialization; a freeze is not a result or selection lock.
import {readFile,writeFile,readdir} from 'node:fs/promises';
import {dirname,join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {TASK_SPEC_SHA256} from './tasks.mjs';
const root=dirname(fileURLToPath(import.meta.url));
export const sha=body=>createHash('sha256').update(body).digest('hex');
export const canonical=x=>JSON.stringify(x,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
export async function freezeProtocol(output=join(root,'protocol-freeze.json')) {
 const bytes=await readFile(join(root,'protocol.json')), protocol=JSON.parse(bytes);
 if(protocol.populations.taskSpecSha256!==TASK_SPEC_SHA256)throw Error('Task specification differs from protocol');
 const sourceHashes={};
 for(const name of (await readdir(root)).filter(n=>/\.(mjs|py)$/.test(n)&&!n.startsWith('test_')).sort())sourceHashes[name]=sha(await readFile(join(root,name)));
 const record={schema:'gamma.channel-gain-protocol-freeze/v1',createdAt:new Date().toISOString(),protocolSha256:sha(bytes),taskSpecSha256:TASK_SPEC_SHA256,exposureRegistrySha256:sha(await readFile(join(root,'exposure-registry.json'))),sourceHashes,modelExecuted:false,selectionCompleted:false,confirmationEvaluated:false};
 record.freezeSha256=sha(canonical(record));
 await writeFile(output,JSON.stringify(record,null,2)+'\n',{flag:'wx'});return record;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))console.log(JSON.stringify(await freezeProtocol(process.argv[2]),null,2));
