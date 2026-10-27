// Original candidate. Contract: https://leetcode.com/problems/count-strictly-increasing-subarrays/
"use strict";
function solve(nums){let run=0,ans=0;for(let i=0;i<nums.length;i++){run=i&&nums[i-1]<nums[i]?run+1:1;ans+=run;}return ans;}
module.exports = solve;
