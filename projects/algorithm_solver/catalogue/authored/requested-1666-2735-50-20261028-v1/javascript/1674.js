"use strict";
function solve(nums,limit){const delta=new Int32Array(2*limit+3);for(let i=0;i<nums.length/2;i++){const a=nums[i],b=nums[nums.length-1-i];delta[2]+=2;delta[1+Math.min(a,b)]--;delta[a+b]--;delta[a+b+1]++;delta[limit+Math.max(a,b)+1]++;}let current=0,answer=nums.length;for(let s=2;s<=2*limit;s++){current+=delta[s];answer=Math.min(answer,current);}return answer;}

function minMoves(nums, limit){return solve(nums, limit);}
module.exports=solve;
module.exports.minMoves=minMoves;
