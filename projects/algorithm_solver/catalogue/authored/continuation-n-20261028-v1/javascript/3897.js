"use strict";
function solve(nums1, nums0) {
const modulus=1000000007n;let total=0;for(let i=0;i<nums1.length;i++)total+=nums1[i]+nums0[i];const powers=[1n];for(let i=0;i<total;i++)powers.push(powers[i]*2n%modulus);function kind(i){return nums0[i]===0?0:nums1[i]===0?2:1;}const indices=nums1.map((_,i)=>i).sort((i,j)=>kind(i)-kind(j)||(kind(i)===1?(nums1[j]-nums1[i]||nums0[i]-nums0[j]):0));let answer=0n;for(const i of indices){const a=nums1[i],b=nums0[i];answer=(answer*powers[a+b]+(powers[a]-1n)*powers[b])%modulus;}return Number(answer);
}
function maxValue(nums1, nums0) { return solve(nums1, nums0); }
module.exports=solve;
module.exports.maxValue=maxValue;
