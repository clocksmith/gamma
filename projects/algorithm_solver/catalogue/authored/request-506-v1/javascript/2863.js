// Original candidate. Contract: https://leetcode.com/problems/maximum-length-of-semi-decreasing-subarrays/
"use strict";
function solve(nums){const s=[];for(let i=0;i<nums.length;i++)if(!s.length||nums[i]>nums[s[s.length-1]])s.push(i);let a=0;for(let j=nums.length-1;j>=0;j--)while(s.length&&nums[s[s.length-1]]>nums[j])a=Math.max(a,j-s.pop()+1);return a;}
module.exports = solve;
