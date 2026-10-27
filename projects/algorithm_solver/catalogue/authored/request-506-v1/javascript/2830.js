// Original candidate implementation. Contract: https://leetcode.com/problems/maximize-the-profit-as-the-salesman/
"use strict";
function solve(n,offers){const ends=Array.from({length:n},()=>[]),dp=Array(n+1).fill(0);for(const [s,e,g] of offers)ends[e].push([s,g]);for(let e=0;e<n;e++){dp[e+1]=dp[e];for(const [s,g] of ends[e])dp[e+1]=Math.max(dp[e+1],dp[s]+g);}return dp[n];}
module.exports = solve;
