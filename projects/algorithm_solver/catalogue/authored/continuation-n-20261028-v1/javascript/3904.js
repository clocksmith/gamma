"use strict";
function solve(nums, k) {
const suffix=Array(nums.length);suffix[nums.length-1]=nums[nums.length-1];for(let i=nums.length-2;i>=0;i--)suffix[i]=Math.min(nums[i],suffix[i+1]);let maximum=0;for(let i=0;i<nums.length;i++){maximum=Math.max(maximum,nums[i]);if(maximum-suffix[i]<=k)return i;}return -1;
}
function firstStableIndex(nums, k) { return solve(nums, k); }
module.exports=solve;
module.exports.firstStableIndex=firstStableIndex;
