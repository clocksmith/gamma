// Original candidate implementation. Contract: https://leetcode.com/problems/minimum-operations-to-make-median-of-array-equal-to-k/
"use strict";
function solve(nums,k){const a=[...nums].sort((a,b)=>a-b),m=Math.floor(a.length/2);let out=0;for(let i=0;i<=m;i++)out+=Math.max(0,a[i]-k);for(let i=m;i<a.length;i++)out+=Math.max(0,k-a[i]);return out;}
module.exports = solve;
