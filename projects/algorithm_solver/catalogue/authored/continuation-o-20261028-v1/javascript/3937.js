"use strict";
function solve(nums, k) {
const costs=[Array(k).fill(0),Array(k).fill(0)];for(let i=0;i<nums.length;i++){const current=nums[i]%k;for(let target=0;target<k;target++){const difference=Math.abs(current-target);costs[i%2][target]+=Math.min(difference,k-difference);}}let answer=Infinity;for(let x=0;x<k;x++)for(let y=0;y<k;y++)if(x!==y)answer=Math.min(answer,costs[0][x]+costs[1][y]);return answer;
}
function minOperations(nums, k) { return solve(nums, k); }
module.exports=solve;
module.exports.minOperations=minOperations;
