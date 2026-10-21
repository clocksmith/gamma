"use strict";
const assert=require('node:assert/strict');const {fragments}=require('./fragment-proposals.cjs');
let checks=0;
for(const source of ['function solve(a){return a+1;}','const solve=a=>a+1;']){
 const p=fragments(source);
 for(const forbidden of [source,'return a+1;','{return a+1;}','a+1']){assert(!p.fragments.includes(forbidden));checks++;}
}
const helper='function h(a){let r=0;for(const x of a)r+=x;return r;}';
const p=fragments(helper+'function solve(a){return h(a)+1;}');assert(p.fragments.includes(helper));checks++;
assert(!p.fragments.includes('h(a)+1'));checks++;
console.log(JSON.stringify({passed:checks}));
