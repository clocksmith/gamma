"use strict";
function solve(nums) {
let answer=0;for(let i=1;i<nums.length;i++)answer+=Math.max(0,nums[i-1]-nums[i]);return answer;
}
function minOperations(nums) { return solve(nums); }
module.exports=solve;
module.exports.minOperations=minOperations;
