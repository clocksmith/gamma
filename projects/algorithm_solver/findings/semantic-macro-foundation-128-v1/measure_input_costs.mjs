import fs from 'node:fs';
import {createRequire} from 'node:module';
import {encodeAscii as jsEncode, PROFILE_ID as JS_PROFILE} from '/home/x/deco/256one/public/labs/two-button/binary-javascript.js';
import {encodeAscii as pyEncode, PROFILE_ID as PY_PROFILE} from '/home/x/deco/256one/public/labs/two-button/binary-python.js';
import {TwoButtonEditor} from '/home/x/deco/256one/public/labs/two-button/editor.js';
const require=createRequire(import.meta.url),acorn=require('/home/x/deco/reploid/node_modules/acorn');
const root='/home/x/deco/gamma/projects/algorithm_solver/runs/semantic-macro-foundation-128-v1';
const seal=JSON.parse(fs.readFileSync(root+'/source-seal.json','utf8'));const rows=[];
for(const row of seal){const source=fs.readFileSync(root+'/'+row.source_file,'utf8'),encoded=(row.language==='javascript'?jsEncode:pyEncode)(source);let editor=new TwoButtonEditor();editor.switchMode(row.language);for(const bit of encoded.bits)editor.enterBit(bit);if(editor.text!==source)throw Error('Lexical roundtrip mismatch');
 let ast=null;if(row.language==='javascript'){const counts={};function visit(x){if(!x||typeof x!=='object')return;if(typeof x.type==='string')counts[x.type]=(counts[x.type]||0)+1;for(const v of Object.values(x)){if(Array.isArray(v))v.forEach(visit);else if(v&&typeof v==='object')visit(v);}}visit(acorn.parse(source,{ecmaVersion:2022}));ast={parser:'Acorn '+acorn.version,total:Object.values(counts).reduce((a,b)=>a+b,0),by_type:counts};}
 rows.push({id:row.id,macro:row.cost,source_bytes:Buffer.byteLength(source),literal_ascii7_bits:source.length*7,literal_byte8_bits:Buffer.byteLength(source)*8,lexical_profile:row.language==='javascript'?JS_PROFILE:PY_PROFILE,lexical_bits:encoded.bits.length,lexical_editor_roundtrip:true,expanded_source_ast:ast});}
const output={scope:'Complete normalized source includes runtime input/numeric guards; all those bytes count. ASCII7 is a literal character-count baseline, not a replay of the legacy smart-indent editor. Lexical8 costs are verified through its current default editor.',rows};
fs.writeFileSync('/home/x/deco/gamma/projects/algorithm_solver/findings/semantic-macro-foundation-128-v1/input-costs.json',JSON.stringify(output,null,2)+'\n');console.log(JSON.stringify(output));
