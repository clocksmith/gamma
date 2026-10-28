"use strict";
function solve(nums) {
const suffix=Array(nums.length);suffix[nums.length-1]=nums[nums.length-1];for(let i=nums.length-2;i>=0;i--)suffix[i]=Math.min(nums[i],suffix[i+1]);let total=0,answer=-Infinity;for(let i=0;i+1<nums.length;i++){total+=nums[i];answer=Math.max(answer,total-suffix[i+1]);}return answer;
}
function maximumScore(nums) { return solve(nums); }
module.exports=solve;
module.exports.maximumScore=maximumScore;
