// Original implementation. Contract: https://leetcode.com/problems/substrings-that-begin-and-end-with-the-same-letter/
"use strict";
function solve(s){const c=Array(26).fill(0);for(const x of s)c[x.charCodeAt(0)-97]++;return c.reduce((a,x)=>a+x*(x+1)/2,0);}
module.exports = solve;
