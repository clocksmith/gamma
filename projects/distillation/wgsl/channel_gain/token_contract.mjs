// Exact spans for the existing tokenizer/formatter; never approximate offsets.
import { createHash } from 'node:crypto';
const sha = value => createHash('sha256').update(value).digest('hex');
const same = (a,b) => a.length===b.length && a.every((v,i)=>v===b[i]);
export function tokenContract({ row, render, encode }) {
  if (typeof render!=='function' || typeof encode!=='function') throw Error('Existing formatter and tokenizer required');
  const {prompt,instructionSpan:s}=row;
  if(typeof prompt!=='string'||!s||!Number.isInteger(s.start)||!Number.isInteger(s.end)||s.start<0||s.end<=s.start||s.end>prompt.length) throw Error('Invalid instruction character span');
  if(sha(prompt)!==row.promptSha256||sha(prompt.slice(s.start,s.end))!==s.textSha256) throw Error('Prompt/span hash mismatch');
  const rendered=render(prompt), contentStart=rendered.indexOf(prompt);
  if(contentStart<0||rendered.indexOf(prompt,contentStart+1)>=0) throw Error('Formatter must preserve exactly one content span');
  const strings=[rendered.slice(0,contentStart),prompt.slice(0,s.start),prompt.slice(s.start,s.end),prompt.slice(s.end),rendered.slice(contentStart+prompt.length)];
  const ids=text=>{const v=Array.from(encode(text));if(v.some(i=>!Number.isInteger(i)||i<0))throw Error('Invalid token ID');return v;};
  const parts=strings.map(ids), full=ids(rendered);
  if(!same(parts.flat(),full))throw Error('Token merges cross a declared span boundary; exact offsets required');
  const start=parts[0].length+parts[1].length, stop=start+parts[2].length;
  if(stop===start)throw Error('Empty instruction token span');
  const referenceIds=[...parts[0],...parts[1],...parts[3],...parts[4]];
  const referenceStart=parts[0].length,referenceStop=referenceStart+parts[1].length+parts[3].length;
  if(referenceStop===referenceStart)throw Error('Reference has no content tokens');
  const templates=(prefix,contentEnd,count)=>[...Array.from({length:prefix},(_,i)=>i),...Array.from({length:count-contentEnd},(_,i)=>contentEnd+i)];
  return Object.freeze({inputIds:Object.freeze(full),span:Object.freeze({start,stop,templatePositions:Object.freeze(templates(parts[0].length,full.length-parts[4].length,full.length))}),referenceIds:Object.freeze(referenceIds),referenceSpan:Object.freeze({start:referenceStart,stop:referenceStop,templatePositions:Object.freeze(templates(referenceStart,referenceStop,referenceIds.length))}),renderedSha256:sha(rendered),tokenIdsSha256:sha(JSON.stringify(full)),referenceTokenIdsSha256:sha(JSON.stringify(referenceIds)),referenceConstruction:'remove exact instruction tokens; retain other token IDs without retokenization'});
}
