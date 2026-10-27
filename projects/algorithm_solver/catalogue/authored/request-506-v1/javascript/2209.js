// Original candidate. Contract: https://leetcode.com/problems/minimum-white-tiles-after-covering-with-carpets/
"use strict";
function solve(floor,numCarpets,carpetLen){const n=floor.length;let dp=Array(n+1).fill(0);for(let i=0;i<n;i++)dp[i+1]=dp[i]+Number(floor[i]);for(let k=0;k<numCarpets;k++){let q=Array(n+1).fill(0);for(let i=1;i<=n;i++)q[i]=Math.min(q[i-1]+Number(floor[i-1]),dp[Math.max(0,i-carpetLen)]);dp=q;}return dp[n];}
module.exports = solve;
