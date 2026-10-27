// Original candidate. Contract: https://leetcode.com/problems/ways-to-split-array-into-good-subarrays/
"use strict";
function solve(nums){let last=-1,ans=1;for(let i=0;i<nums.length;i++)if(nums[i]){if(last>=0)ans=ans*(i-last)%1000000007;last=i;}return last<0?0:ans;}
module.exports = solve;
