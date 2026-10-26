import {controls as inherited} from './controls-v2.mjs';
import {acorn,scope} from '../ast-binding-alignment-v1/parser.mjs';
import {canonicalize} from '../ast-binding-alignment-v1/canonicalize.mjs';
import {containerSubset,checkAlphaPostcondition} from './proof-v2.mjs';
function directive(source){const ast=acorn.parse(source,{ecmaVersion:2022,ranges:true});const manager=scope.analyze(ast,{ecmaVersion:2022,sourceType:'script',optimistic:false,ignoreEval:false});return {strict:manager.scopes.find(s=>s.type==='function').isStrict,spelling:ast.body[0].body.body[0].directive};}
export function controls(){
 const rows=inherited();
 for(const [name,source,expectedStrict] of [
  ['escaped_strict_not_promoted',String.raw`function solve(a){"use\x20strict";const m=new Map();m.set(a,1);return m.has(a);}`,false],
  ['genuine_strict_preserved','function solve(a){"use strict";const m=new Map();m.set(a,1);return m.has(a);}',true]
 ]){
  const before=directive(source);let observed=containerSubset(source).syntactic_candidate&&before.strict===expectedStrict;
  for(const mode of ['format','role']){const transformed=canonicalize(source,mode);checkAlphaPostcondition(source,transformed.source);const after=directive(transformed.source);observed=observed&&after.strict===expectedStrict&&after.spelling===before.spelling;}
  rows.push({name,expected:true,observed,alpha_structure_verified:observed,reasons:[]});
 }
 return rows;
}
