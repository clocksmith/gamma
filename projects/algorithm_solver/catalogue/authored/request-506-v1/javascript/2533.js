// Original candidate implementation. Contract: https://leetcode.com/problems/number-of-good-binary-strings/
"use strict";
function solve(minLength,maxLength,oneGroup,zeroGroup){const mod=1000000007,dp=Array(maxLength+1).fill(0);dp[0]=1;let answer=0;for(let n=1;n<=maxLength;n++){if(n>=oneGroup)dp[n]+=dp[n-oneGroup];if(n>=zeroGroup)dp[n]+=dp[n-zeroGroup];dp[n]%=mod;if(n>=minLength)answer=(answer+dp[n])%mod;}return answer;}
module.exports = solve;
