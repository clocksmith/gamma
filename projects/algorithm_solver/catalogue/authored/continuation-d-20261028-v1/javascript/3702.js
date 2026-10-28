"use strict";
// Original development candidate; qualification pending.
function solve(nums) {
let total=0, nonzero=false; for(const value of nums){total^=value; nonzero ||= value!==0;} return total ? nums.length : nonzero ? nums.length-1 : 0;
}
function longestSubsequence(nums) { return solve(nums); }
module.exports = solve;
module.exports.longestSubsequence = longestSubsequence;
