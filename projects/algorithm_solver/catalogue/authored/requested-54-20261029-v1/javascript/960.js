"use strict";
function solve(strs){const width=strs[0].length,dp=Array(width).fill(1);for(let j=0;j<width;j++)for(let i=0;i<j;i++)if(strs.every(row=>row[i]<=row[j]))dp[j]=Math.max(dp[j],dp[i]+1);return width-Math.max(...dp);}

function minDeletionSize(strs) { return solve(strs); }
module.exports=solve;
module.exports.minDeletionSize=minDeletionSize;
