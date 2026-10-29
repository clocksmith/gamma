"use strict";
function solve(nums,k){const windows=[];let total=0;for(let i=0;i<k;i++)total+=nums[i];windows.push(total);for(let i=k;i<nums.length;i++){total+=nums[i]-nums[i-k];windows.push(total);}const size=windows.length,left=new Array(size),right=new Array(size);let best=0;for(let i=0;i<size;i++){if(windows[i]>windows[best])best=i;left[i]=best;}best=size-1;for(let i=size-1;i>=0;i--){if(windows[i]>=windows[best])best=i;right[i]=best;}let answer=null,bestTotal=-1;for(let m=k;m<size-k;m++){const a=left[m-k],c=right[m+k],value=windows[a]+windows[m]+windows[c];if(value>bestTotal){bestTotal=value;answer=[a,m,c];}}return answer;}

function maxSumOfThreeSubarrays(nums, k){return solve(nums, k);}
module.exports=solve;
module.exports.maxSumOfThreeSubarrays=maxSumOfThreeSubarrays;
