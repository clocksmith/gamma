"use strict";
const assert=require('assert'),{aliasEdges}=require('./harness.cjs');
const a=[1,2],b=[3,4];
assert.deepStrictEqual(aliasEdges([a],a),[['result','args.0']]);
assert.deepStrictEqual(aliasEdges([a],a.slice()),[]);
assert.deepStrictEqual(aliasEdges([[a,b]],[a,[7,8],b]),[['result.0','args.0.0'],['result.2','args.0.1']]);
assert.deepStrictEqual(aliasEdges([], [a,a]),[['result.1','result.0']]);
console.log('4 alias topology checks passed');
