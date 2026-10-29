"use strict";
function solve(nums,k){const values=[...nums].sort((a,b)=>a-b);let low=0,high=values[values.length-1]-values[0];while(low<high){const d=Math.floor((low+high)/2);let left=0,count=0;for(let right=0;right<values.length;right++){while(values[right]-values[left]>d)left++;count+=right-left;}if(count>=k)high=d;else low=d+1;}return low;}

function smallestDistancePair(nums, k){return solve(nums, k);}
module.exports=solve;
module.exports.smallestDistancePair=smallestDistancePair;
