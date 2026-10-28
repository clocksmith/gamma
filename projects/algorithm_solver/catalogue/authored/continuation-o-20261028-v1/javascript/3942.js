"use strict";
function solve(nums) {
const n=nums.length,zero=nums.indexOf(0);let ascending=true,descending=true;for(let i=0;i<n;i++){if(nums[(zero+i)%n]!==i)ascending=false;if(nums[(zero-i+n)%n]!==i)descending=false;}let answer=n+3;if(ascending)answer=Math.min(zero,n-zero+2);if(descending){const rotations=n-1-zero;answer=Math.min(answer,1+Math.min(rotations,n-rotations));}return answer<=n+2?answer:-1;
}
function minOperations(nums) { return solve(nums); }
module.exports=solve;
module.exports.minOperations=minOperations;
