// Original candidate. Contract: https://leetcode.com/problems/maximum-number-that-makes-result-of-bitwise-and-zero/
"use strict";
function solve(n){let p=1n,v=BigInt(n);while((p<<1n)<=v)p<<=1n;return Number(p-1n);}
module.exports = solve;
