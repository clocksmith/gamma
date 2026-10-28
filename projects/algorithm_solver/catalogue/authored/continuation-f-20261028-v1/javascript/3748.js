"use strict";
function solve(nums, queries) {
const n=nums.length,ends=Array(n).fill(n-1),prefix=[0];for(let i=n-2;i>=0;i--)ends[i]=nums[i]<=nums[i+1]?ends[i+1]:i;for(let i=0;i<n;i++)prefix.push(prefix[i]+ends[i]-i+1);return queries.map(([left,right])=>{let lo=left,hi=right+1;while(lo<hi){const mid=Math.floor((lo+hi)/2);if(ends[mid]<=right)lo=mid+1;else hi=mid;}const length=right-lo+1;return prefix[lo]-prefix[left]+length*(length+1)/2;});
}
function countStableSubarrays(nums, queries) { return solve(nums, queries); }
module.exports=solve;
module.exports.countStableSubarrays=countStableSubarrays;
