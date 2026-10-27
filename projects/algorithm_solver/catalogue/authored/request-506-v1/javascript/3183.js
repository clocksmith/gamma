// Original candidate implementation. Contract: https://leetcode.com/problems/the-number-of-ways-to-make-the-sum/
"use strict";
function solve(n){const mod=1000000007,dp=Array(n+1).fill(0);dp[0]=1;for(const c of [1,2,6])for(let t=c;t<=n;t++)dp[t]=(dp[t]+dp[t-c])%mod;let answer=0;for(let c=0;c<=2&&4*c<=n;c++)answer=(answer+dp[n-4*c])%mod;return answer;}
module.exports = solve;
