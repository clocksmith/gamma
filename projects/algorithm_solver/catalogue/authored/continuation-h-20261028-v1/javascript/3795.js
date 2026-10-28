"use strict";
function solve(nums, k) {
const counts=new Map();let total=0,left=0,best=nums.length+1;for(let right=0;right<nums.length;right++){const value=nums[right];if(!(counts.get(value)||0))total+=value;counts.set(value,(counts.get(value)||0)+1);while(total>=k){best=Math.min(best,right-left+1);const outgoing=nums[left++],count=counts.get(outgoing)-1;counts.set(outgoing,count);if(count===0)total-=outgoing;}}return best<=nums.length?best:-1;
}
function minLength(nums, k) { return solve(nums, k); }
module.exports=solve;
module.exports.minLength=minLength;
