"use strict";
function solve(nums) {
let peak=0;for(let i=1;i<nums.length;i++)if(nums[i]>nums[peak])peak=i;let left=0,right=0;for(let i=0;i<peak;i++)left+=nums[i];for(let i=peak+1;i<nums.length;i++)right+=nums[i];return left>right?0:right>left?1:-1;
}
function compareBitonicSums(nums) { return solve(nums); }
module.exports=solve;
module.exports.compareBitonicSums=compareBitonicSums;
