import {readFile,stat} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
export async function checkCompletion(path,expected){
 let bytes;try{bytes=await readFile(path);}catch(error){if(error.code==='ENOENT')return{ready:false,reason:'receipt_missing'};throw error;}
 let receipt;try{receipt=JSON.parse(bytes);}catch(error){if(error instanceof SyntaxError)return{ready:false,reason:'receipt_write_incomplete'};throw error;}
 if(receipt.status!==expected.confirmationStatus||receipt.confirmationEvaluated!==true)return{ready:false,reason:'confirmation_not_terminal'};
 const{receiptSha256,...body}=receipt;
 if(createHash('sha256').update(JSON.stringify(canonical(body))).digest('hex')!==receiptSha256)throw Error('Confirmation receipt checksum mismatch');
 for(const key of ['runtimeLockSha256','stageLockSha256'])if(receipt[key]!==expected[key])throw Error(`Confirmation ${key} mismatch`);
 if(!Array.isArray(receipt.generated?.requests)||receipt.generated.requests.length!==expected.confirmationRequests)throw Error('Confirmation request count mismatch');
 return{ready:true,receiptSha256,receiptFileSha256:createHash('sha256').update(bytes).digest('hex'),requestCount:receipt.generated.requests.length,runtimeLockSha256:receipt.runtimeLockSha256,stageLockSha256:receipt.stageLockSha256};
}
export async function checkInheritedExclusiveLock(fd,path){
 if(process.platform!=='linux'||!Number.isInteger(fd)||fd<3)throw Error('Inherited Linux exclusive timing-lock FD required');
 const [held,target,info]=await Promise.all([stat(`/proc/self/fd/${fd}`),stat(path),readFile(`/proc/self/fdinfo/${fd}`,'utf8')]);
 if(held.dev!==target.dev||held.ino!==target.ino||!held.isFile())throw Error('Inherited timing-lock FD points at another file');
 if(!/^lock:\s+\d+:\s+FLOCK\s+ADVISORY\s+WRITE\s/m.test(info))throw Error('Inherited timing-lock FD has no exclusive flock');
 return{mode:'exclusive',path,fd,device:held.dev,inode:held.ino,checkedAt:new Date().toISOString(),globalIsolationQualified:false};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{const schedule=JSON.parse(await readFile(process.argv[2]));console.log(JSON.stringify(await checkCompletion(schedule.confirmationReceipt,schedule.confirmationContract)));}
 catch(error){console.error(error.stack??String(error));process.exitCode=2;}
}
