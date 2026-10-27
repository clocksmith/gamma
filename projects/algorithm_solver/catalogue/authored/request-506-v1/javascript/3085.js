// Original implementation. Contract: https://leetcode.com/problems/minimum-deletions-to-make-string-k-special/
"use strict";
function solve(word,k){const c=Array(26).fill(0);for(const x of word)c[x.charCodeAt(0)-97]++;const a=c.filter(x=>x>0);return Math.min(...a.map(low=>a.reduce((s,x)=>s+(x<low?x:Math.max(0,x-low-k)),0)));}
module.exports = solve;
