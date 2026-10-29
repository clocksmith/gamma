"use strict";
function solve(nums,k){const total=nums.reduce((a,b)=>a+b,0),diffs=[],right=new Map(),left=new Map();let prefix=0;for(let i=0;i<nums.length-1;i++){prefix+=nums[i];const d=2*prefix-total;diffs.push(d);right.set(d,(right.get(d)||0)+1);}let answer=right.get(0)||0;for(let i=0;i<nums.length;i++){const delta=k-nums[i];answer=Math.max(answer,(left.get(delta)||0)+(right.get(-delta)||0));if(i<diffs.length){const d=diffs[i];right.set(d,right.get(d)-1);left.set(d,(left.get(d)||0)+1);}}return answer;}

function waysToPartition(nums, k){return solve(nums, k);}
module.exports=solve;
module.exports.waysToPartition=waysToPartition;
