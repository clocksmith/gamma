// Original candidate implementation. Contract: https://leetcode.com/problems/sum-of-digit-differences-of-all-pairs/
"use strict";
function solve(nums){const counts=Array.from({length:String(nums[0]).length},()=>Array(10).fill(0));let answer=0;for(let i=0;i<nums.length;i++){const s=String(nums[i]);for(let j=0;j<s.length;j++){const d=+s[j];answer+=i-counts[j][d];counts[j][d]++;}}return answer;}
module.exports = solve;
