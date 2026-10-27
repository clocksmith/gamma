// Original implementation. Contract: https://leetcode.com/problems/minimum-number-of-operations-to-make-arrays-similar/
"use strict";
function solve(nums,target){const cmp=(a,b)=>(a%2-b%2)||(a-b),a=[...nums].sort(cmp),b=[...target].sort(cmp);return a.reduce((s,x,i)=>s+Math.abs(x-b[i]),0)/4;}
module.exports = solve;
