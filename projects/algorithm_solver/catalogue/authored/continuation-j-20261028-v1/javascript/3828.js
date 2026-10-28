"use strict";
function solve(nums) {
return Math.max(nums[0],nums[nums.length-1]);
}
function finalElement(nums) { return solve(nums); }
module.exports=solve;
module.exports.finalElement=finalElement;
