'use strict';
// Trusted synthetic transport-only test. Never imports submitted source.
const assert=require('assert'),h=require('./harness.cjs');
function old(args,result){const seen=new WeakMap(),edges=[];function walk(v,p){if(v===null||typeof v!=='object')return;if(seen.has(v)){edges.push([p,seen.get(v)]);return;}seen.set(v,p);for(const[k,x]of Object.entries(v))walk(x,p+'.'+k);}walk(args,'args');walk(result,'result');return edges;}
const shared=[],cycle=[];cycle.push(cycle);const node={val:1,left:null,right:null};node.left=node;
for(const[a,r]of[[[],[]],[[shared,shared],shared],[[cycle],cycle],[[node],node],[[{x:shared,y:[shared]}],{a:shared}]])assert.deepStrictEqual(h.aliases(a,r),old(a,r));
const a=[0];for(let i=0;i<8499;i++)a.push(0,null);a.pop();const tag={__tree_node__:a},tree=h.decode(tag);assert.deepStrictEqual(h.encode(tree),tag);assert.deepStrictEqual(h.aliases([tree],'a'.repeat(8500)),[]);
let leaf=tree;for(let i=0;i<50;i++)leaf=leaf.left;assert.deepStrictEqual(h.aliases([tree],leaf),[['result','args.0'+'.left'.repeat(50)]]);
console.log(JSON.stringify({passed:7,scope:'trusted synthetic alias-order and deep-tree transport only',candidate_executions:0}));
