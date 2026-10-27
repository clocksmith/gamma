// Original candidate implementation. Contract: https://leetcode.com/problems/visit-array-positions-to-maximize-score/
"use strict";
function solve(nums,x){const best=[-Infinity,-Infinity];best[nums[0]%2]=nums[0];for(let i=1;i<nums.length;i++){const v=nums[i],p=v%2;best[p]=Math.max(best[p],best[1-p]-x)+v;}return Math.max(...best);}
module.exports = solve;
