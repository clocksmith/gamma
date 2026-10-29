"use strict";
function solve(nums){const p=[0];for(const v of nums)p.push(p[p.length-1]+v);const n=nums.length;let lower=2,upper=2,answer=0;for(let first=1;first<n-1;first++){lower=Math.max(lower,first+1);while(lower<n&&p[lower]<2*p[first])lower++;upper=Math.max(upper,lower);while(upper<n&&2*p[upper]<=p[n]+p[first])upper++;answer=(answer+upper-lower)%1000000007;}return answer;}

function waysToSplit(nums){return solve(nums);}
module.exports=solve;
module.exports.waysToSplit=waysToSplit;
