// Original candidate implementation. Contract: https://leetcode.com/problems/maximum-number-of-removal-queries-that-can-be-processed-i/
"use strict";
function solve(nums,queries){const n=nums.length,m=queries.length,dp=Array.from({length:n},()=>new Int32Array(n).fill(-1));dp[0][n-1]=0;let answer=0;for(let len=n;len>0;len--)for(let l=0;l+len<=n;l++){const r=l+len-1,t=dp[l][r];if(t<0)continue;if(t===m)return m;const a=t+Number(nums[l]>=queries[t]),b=t+Number(nums[r]>=queries[t]);answer=Math.max(answer,a,b);if(len>1){dp[l+1][r]=Math.max(dp[l+1][r],a);dp[l][r-1]=Math.max(dp[l][r-1],b);}}return answer;}
module.exports = solve;
