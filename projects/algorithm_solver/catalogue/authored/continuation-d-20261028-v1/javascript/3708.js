"use strict";
// Original development candidate; qualification pending.
function solve(nums) {
let best=2,run=2;for(let i=2;i<nums.length;i++){run=nums[i]===nums[i-1]+nums[i-2]?run+1:2;best=Math.max(best,run);}return best;
}
function longestSubarray(nums) { return solve(nums); }
module.exports = solve;
module.exports.longestSubarray = longestSubarray;
