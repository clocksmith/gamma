import assert from 'node:assert/strict';
import {lower} from './lower.mjs';
let count=0;
const source=(body,params='value',extra='')=>`function helper(x){ return x; }\nclass Solution { method(${params}) {${body}} ${extra}}\nfunction solve(...args){return new Solution().method(...args);}\n`;
const good=lower(source('return helper(value);'));assert(good.ast_verified);assert(good.helpers_verbatim);assert(good.source.includes('function helper(x){ return x; }'));assert(good.source.includes('"use strict";'));assert(good.lowered_bytes<good.source_bytes);count++;
assert(lower('class Box{constructor(x){this.x=x;}}\n'+source('return new Box(value);')).helpers_verbatim);count++;
const exact='let n=9007199254740993n; return [n,/a+/gi,`x${value}`,arguments.length];';assert(lower(source(exact)).source.includes(exact));count++;
assert(lower(source('"use strict";return value;')).ast_verified);count++;
for(const text of [source('return this.x;'),source('return new.target;'),source('return Solution;'),source('return solve(value);'),source('return value.name;'),source('return value["constructor"];'),source('return eval(value);'),source('return value;','value=1'),source('return value;','...value'),source('return value;','value','other(){}'),source('return value;').replace('new Solution().method(...args)','new Solution().method(args)'),source('return value;').replace('class Solution {','class Solution extends Object {')]){assert.throws(()=>lower(text));count++;}
console.log(JSON.stringify({synthetic_lowering_tests:count,candidate_executions:0}));
