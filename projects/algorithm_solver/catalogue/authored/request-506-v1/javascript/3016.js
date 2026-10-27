// Original implementation. Contract: https://leetcode.com/problems/minimum-number-of-pushes-to-type-word-ii/
"use strict";
function solve(word){const c=Array(26).fill(0);for(const x of word)c[x.charCodeAt(0)-97]++;c.sort((a,b)=>b-a);return c.reduce((s,x,i)=>s+x*(Math.floor(i/8)+1),0);}
module.exports = solve;
