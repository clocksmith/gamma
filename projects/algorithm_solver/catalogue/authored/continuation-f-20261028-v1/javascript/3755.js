"use strict";
function solve(nums) {
const earliest=new Map([['0,0',-1]]);let xor=0,balance=0,answer=0;for(let i=0;i<nums.length;i++){xor^=nums[i];balance+=nums[i]%2===0?1:-1;const key=xor+','+balance;if(earliest.has(key))answer=Math.max(answer,i-earliest.get(key));else earliest.set(key,i);}return answer;
}
function maxBalancedSubarray(nums) { return solve(nums); }
module.exports=solve;
module.exports.maxBalancedSubarray=maxBalancedSubarray;
