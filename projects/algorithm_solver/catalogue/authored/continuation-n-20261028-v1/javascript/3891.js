"use strict";
function solve(nums) {
function better(a,b){return a[0]>b[0]||(a[0]===b[0]&&a[1]<=b[1])?a:b;}let skipped=[0,0],selected=[-1,0];for(let i=1;i+1<nums.length;i++){const cost=Math.max(0,Math.max(nums[i-1],nums[i+1])+1-nums[i]),nextSelected=[skipped[0]+1,skipped[1]+cost];skipped=better(skipped,selected);selected=nextSelected;}return better(skipped,selected)[1];
}
function minIncrease(nums) { return solve(nums); }
module.exports=solve;
module.exports.minIncrease=minIncrease;
