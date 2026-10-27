// Original candidate. Contract: https://leetcode.com/problems/elements-in-array-after-removing-and-replacing-elements/
"use strict";
function solve(nums,queries){const n=nums.length;return queries.map(([t,i])=>{t%=2*n;return t<n?(t+i<n?nums[t+i]:-1):(i<t-n?nums[i]:-1);});}
module.exports = solve;
