"use strict";
function solve(nums) {
let maximum=1;for(const value of nums)maximum=Math.max(maximum,value);const limit=Math.max(2,maximum*2),prime=new Uint8Array(limit+1).fill(1);prime[0]=prime[1]=0;for(let value=2;value*value<=limit;value++)if(prime[value])for(let multiple=value*value;multiple<=limit;multiple+=value)prime[multiple]=0;const following=new Int32Array(limit+1);let nextPrime=limit+1;for(let value=limit;value>=0;value--){if(prime[value])nextPrime=value;following[value]=nextPrime;}let answer=0;for(let i=0;i<nums.length;i++){const value=nums[i];if(i%2===0)answer+=following[value]-value;else if(prime[value])answer+=value===2?2:1;}return answer;
}
function minOperations(nums) { return solve(nums); }
module.exports=solve;
module.exports.minOperations=minOperations;
