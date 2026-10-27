// Original candidate implementation. Contract: https://leetcode.com/problems/longest-unequal-adjacent-groups-subsequence-ii/
"use strict";
function solve(words,groups){const n=words.length,dp=Array(n).fill(1),previous=Array(n).fill(-1);let best=0;for(let i=0;i<n;i++){for(let j=0;j<i;j++)if(groups[i]!==groups[j]&&words[i].length===words[j].length){let difference=0;for(let k=0;k<words[i].length;k++)difference+=Number(words[i][k]!==words[j][k]);if(difference===1&&dp[j]+1>dp[i]){dp[i]=dp[j]+1;previous[i]=j;}}if(dp[i]>dp[best])best=i;}const out=[];for(let i=best;i>=0;i=previous[i])out.push(words[i]);return out.reverse();}
module.exports = solve;
