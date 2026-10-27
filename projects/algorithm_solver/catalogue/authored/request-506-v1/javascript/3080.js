// Original candidate. Contract: https://leetcode.com/problems/mark-elements-on-array-by-performing-queries/
"use strict";
function solve(nums,queries){const order=Array.from({length:nums.length},(_,i)=>i).sort((i,j)=>nums[i]-nums[j]||i-j),seen=new Uint8Array(nums.length),out=[];let total=nums.reduce((s,x)=>s+x,0),j=0;for(const[index,count]of queries){let k=count;if(!seen[index]){seen[index]=1;total-=nums[index];}while(k&&j<order.length){const i=order[j++];if(!seen[i]){seen[i]=1;total-=nums[i];k--;}}out.push(total);}return out;}
module.exports = solve;
