"use strict";
// Original development candidate; qualification pending.
function solve(nums) {
let best=0;for(let left=0;left<nums.length;left++){const seen=new Set();let balance=0;for(let right=left;right<nums.length;right++){const value=nums[right];if(!seen.has(value)){seen.add(value);balance+=value%2===0?1:-1;}if(balance===0)best=Math.max(best,right-left+1);}}return best;
}
function longestBalanced(nums) { return solve(nums); }
module.exports = solve;
module.exports.longestBalanced = longestBalanced;
