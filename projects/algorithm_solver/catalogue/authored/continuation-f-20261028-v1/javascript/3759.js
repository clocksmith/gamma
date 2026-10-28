"use strict";
function solve(nums, k) {
if(k===0)return nums.length;const sorted=nums.slice().sort((a,b)=>a-b),cutoff=sorted[nums.length-k];let answer=0;for(const value of nums)if(value<cutoff)answer++;return answer;
}
function countElements(nums, k) { return solve(nums, k); }
module.exports=solve;
module.exports.countElements=countElements;
