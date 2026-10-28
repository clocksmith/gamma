"use strict";
function solve(nums) {
let limit=0;for(const value of nums)limit+=value;const suffix=Array(nums.length+1).fill(1);for(let i=nums.length-1;i>=0;i--)suffix[i]=suffix[i+1]>Math.floor(limit/nums[i])?limit+1:suffix[i+1]*nums[i];let left=0;for(let i=0;i<nums.length;i++){if(left===suffix[i+1])return i;left+=nums[i];}return -1;
}
function smallestBalancedIndex(nums) { return solve(nums); }
module.exports=solve;
module.exports.smallestBalancedIndex=smallestBalancedIndex;
