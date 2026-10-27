// Original candidate. Contract: https://leetcode.com/problems/largest-element-in-an-array-after-merge-operations/
"use strict";
function solve(nums){let s=nums[nums.length-1],ans=s;for(let i=nums.length-2;i>=0;i--){s=nums[i]<=s?s+nums[i]:nums[i];ans=Math.max(ans,s);}return ans;}
module.exports = solve;
