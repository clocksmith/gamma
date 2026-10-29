"use strict";
function solve(nums,x){const best=nums.slice();let answer=best.reduce((a,b)=>a+b,0);for(let r=1;r<nums.length;r++){let total=0;for(let i=0;i<nums.length;i++){best[i]=Math.min(best[i],nums[(i+r)%nums.length]);total+=best[i];}answer=Math.min(answer,total+r*x);}return answer;}

function minCost(nums, x){return solve(nums, x);}
module.exports=solve;
module.exports.minCost=minCost;
