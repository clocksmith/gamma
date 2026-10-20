export const PROFILE='gamma.literal-shared7-interactive.v1';
export const DICTIONARY_SHA='62ab89348d4781187375f35663f81b6304a70b9f951d9bd3327fecae6d3b8c39';
export const CONTROLS={125:'Undo last literal',126:'Reset assembled source',127:'Finish'};
export const MAX_BITS=8190, MAX_SOURCE=65536, MAX_EVENTS=16384;
const bytes=text=>new TextEncoder().encode(text);
export async function sha256(value){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',typeof value==='string'?bytes(value):value))].map(x=>x.toString(16).padStart(2,'0')).join('');}
export function dictionaryBytes(literals){
  const values=literals.map(bytes),result=new Uint8Array(8+values.reduce((n,b)=>n+4+b.length,0)),view=new DataView(result.buffer);
  result.set(bytes('LTD1'));view.setUint32(4,literals.length);let at=8;
  for(const value of values){view.setUint32(at,value.length);at+=4;result.set(value,at);at+=value.length;}return result;
}
export async function verifyLanguage(data){
  if(data?.profile!==PROFILE||data.source_commit!=='0951af88c332818133f132cce9d6cf8e277b90cb'||data.dictionary_sha256!==DICTIONARY_SHA||!Array.isArray(data.literals)||data.literals.length!==79||data.literals.some(x=>typeof x!=='string'||!x)||new Set(data.literals).size!==79)throw Error('Literal dictionary identity mismatch');
  if(await sha256(dictionaryBytes(data.literals))!==DICTIONARY_SHA)throw Error('Literal dictionary bytes changed');
  if(!Array.isArray(data.problems)||data.problems.length!==20||new Set(data.problems.map(p=>p.id)).size!==20)throw Error('Invalid problem guides');
  for(const p of data.problems){if(!/^\d{4}$/.test(p.id)||!Array.isArray(p.sequence)||p.sequence.some(i=>!Number.isInteger(i)||i<0||i>=79)||await sha256(p.sequence.map(i=>data.literals[i]).join(''))!==p.source_sha256)throw Error('Guide source identity mismatch');}
  return data;
}
export function inspect(bits,literals){
  if(typeof bits!=='string'||!/^[01]*$/.test(bits)||bits.length>MAX_BITS)throw Error('Invalid or oversized bitstream');
  let selected=[],complete=false,error=null,literalBits=0,controlBits=0,rejectedBits=0;
  const words=Math.floor(bits.length/7),prefix=bits.slice(words*7);
  for(let i=0;i<words;i++){
    const id=parseInt(bits.slice(i*7,i*7+7),2);
    if(error){rejectedBits+=7;continue;}
    if(complete){error='Bits after Finish; undo the extra input.';rejectedBits+=7;continue;}
    if(id<79){selected.push(id);literalBits+=7;if(bytes(selected.map(n=>literals[n]).join('')).length>MAX_SOURCE){selected.pop();error='Assembled source exceeds 64 KiB.';}}
    else if(id===125){controlBits+=7;selected.pop();}
    else if(id===126){controlBits+=7;selected=[];}
    else if(id===127){controlBits+=7;if(!selected.length)error='Cannot finish an empty program.';else complete=true;}
    else {rejectedBits+=7;error=`Unused literal ID ${id}; undo this word. IDs 79–124 are rejected.`;}
  }
  if(complete&&prefix)error='Bits after Finish; undo the extra input.';
  return {selected,source:selected.map(i=>literals[i]).join(''),complete:complete&&!error,error,prefix,literal_bits:literalBits,control_bits:controlBits,rejected_bits:rejectedBits,partial_bits:prefix.length,total_bits:bits.length,source_only_bits:selected.length*7};
}
export class LiteralSession {
  constructor(language,problem){if(!language.problems.some(p=>p.id===problem))throw Error('Unknown literal problem');this.language=language;this.problem=problem;this.bits='';this.events=[];this.tests=[];this.replay=false;}
  snapshot(){return inspect(this.bits,this.language.literals);}
  bit(value){if(this.replay)throw Error('Replay is read-only');if(value!==0&&value!==1)throw Error('Use 0 or 1');if(this.events.length>=MAX_EVENTS||this.bits.length>=MAX_BITS)throw Error('Session input limit');const s=this.snapshot();if(s.complete||s.error)throw Error('Undo input or begin a new session before continuing');this.bits+=value;this.events.push({kind:'bit',value});this.tests=[];}
  backspace(){if(this.replay)throw Error('Replay is read-only');if(this.events.length>=MAX_EVENTS)throw Error('Session input limit');this.bits=this.bits.slice(0,-1);this.events.push({kind:'backspace'});this.tests=[];}
  async report(){const s=this.snapshot(),record={schema:'gamma.literal-session.v1',profile:PROFILE,dictionary_sha256:DICTIONARY_SHA,problem_id:this.problem,events:structuredClone(this.events),bits:this.bits,selections:s.selected,source_sha256:null,complete:s.complete,error:s.error,cost:{literal_bits:s.literal_bits,control_bits:s.control_bits,rejected_bits:s.rejected_bits,partial_bits:s.partial_bits,total_bits:s.total_bits,source_only_bits:s.source_only_bits,entered_bits:this.events.filter(e=>e.kind==='bit').length,undo_bit_actions:this.events.filter(e=>e.kind==='backspace').length},tests:structuredClone(this.tests),claim:'Local replay record, not signed evidence or autonomous synthesis. Imported test receipts are unverified historical records.'};record.source_sha256=await sha256(s.source);return record;}
}
export async function replayRecord(language,record){
  if(record?.schema!=='gamma.literal-session.v1'||record.profile!==PROFILE||record.dictionary_sha256!==DICTIONARY_SHA||!Array.isArray(record.events)||record.events.length>MAX_EVENTS||!Array.isArray(record.tests)||record.tests.length>16)throw Error('Unsupported or oversized replay');
  const session=new LiteralSession(language,record.problem_id);
  for(const e of record.events){if(e?.kind==='bit'&&Object.keys(e).sort().join(',')==='kind,value')session.bit(e.value);else if(e?.kind==='backspace'&&Object.keys(e).join(',')==='kind')session.backspace();else throw Error('Unknown replay action');}
  const expected=await session.report();
  for(const key of ['bits','selections','source_sha256','complete','error','cost'])if(JSON.stringify(record[key])!==JSON.stringify(expected[key]))throw Error(`Replay mismatch: ${key}`);
  session.tests=structuredClone(record.tests);session.replay=true;return session;
}
