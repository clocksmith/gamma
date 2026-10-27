// Original candidate. Contract: https://leetcode.com/problems/find-triangular-sum-of-an-array/
"use strict";
function solve(nums){const a=nums.slice();for(let n=a.length-1;n>0;n--)for(let i=0;i<n;i++)a[i]=(a[i]+a[i+1])%10;return a[0];}
module.exports = solve;
