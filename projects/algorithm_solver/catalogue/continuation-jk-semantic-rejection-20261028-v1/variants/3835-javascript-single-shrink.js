"use strict";
function solve(nums, k) {
const maximum=[],minimum=[];let maxHead=0,minHead=0,left=0,answer=0;for(let right=0;right<nums.length;right++){const value=nums[right];while(maximum.length>maxHead&&nums[maximum[maximum.length-1]]<=value)maximum.pop();while(minimum.length>minHead&&nums[minimum[minimum.length-1]]>=value)minimum.pop();maximum.push(right);minimum.push(right);if((nums[maximum[maxHead]]-nums[minimum[minHead]])*(right-left+1)>k){if(maximum[maxHead]===left)maxHead++;if(minimum[minHead]===left)minHead++;left++;}answer+=right-left+1;}return answer;
}
function countSubarrays(nums, k) { return solve(nums, k); }
module.exports=solve;
module.exports.countSubarrays=countSubarrays;
