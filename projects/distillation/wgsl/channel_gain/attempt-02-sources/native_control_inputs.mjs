import {createHash} from 'node:crypto';
const digest=(seed,domain,index)=>{if(!Number.isSafeInteger(seed)||!Number.isSafeInteger(index)||index<0)throw Error('Exact integer control seed/index required');return createHash('sha256').update(`channel-gain-v1:${domain}:${seed}:${index}`).digest();};
export function controlPermutation(size,seed,domain){if(!Number.isSafeInteger(size)||size<1)throw Error('Positive control dimension required');return Uint32Array.from(Array.from({length:size},(_,i)=>({i,key:digest(seed,domain,i)})).sort((a,b)=>Buffer.compare(a.key,b.key)||a.i-b.i).map(v=>v.i));}
export function shuffleInstruction(ids,span,seed){const result=[...ids],order=controlPermutation(span.stop-span.start,seed,'instruction-tokens');for(let i=0;i<order.length;i++)result[span.start+i]=ids[span.start+order[i]];return result;}
export function randomZInputs(size,seed){return Float32Array.from({length:size},(_,i)=>Number(digest(seed,'random-z',i).readBigUInt64BE(0)>>11n)/2**53*2-1);}
