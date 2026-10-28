"use strict";
function solve(nums, queries) {
const n=nums.length,closest=Array(n);closest[0]=1;closest[n-1]=n-2;for(let i=1;i+1<n;i++)closest[i]=nums[i]-nums[i-1]<=nums[i+1]-nums[i]?i-1:i+1;const forward=[0],backward=[0];for(let i=0;i+1<n;i++){const gap=nums[i+1]-nums[i];forward.push(forward[i]+(closest[i]===i+1?1:gap));backward.push(backward[i]+(closest[i+1]===i?1:gap));}return queries.map(([a,b])=>a<=b?forward[b]-forward[a]:backward[a]-backward[b]);
}
function minCost(nums, queries) { return solve(nums, queries); }
module.exports=solve;
module.exports.minCost=minCost;
