// Original candidate implementation. Contract: https://leetcode.com/problems/maximum-sum-score-of-array/
"use strict";
function solve(nums){const total=nums.reduce((a,b)=>a+b,0);let prefix=0,out=-Infinity;for(const x of nums){out=Math.max(out,total-prefix);prefix+=x;out=Math.max(out,prefix);}return out;}
module.exports = solve;
