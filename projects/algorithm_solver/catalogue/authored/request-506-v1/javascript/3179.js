// Original candidate. Contract: https://leetcode.com/problems/find-the-n-th-value-after-k-seconds/
"use strict";
function solve(n,k){const a=Array(n).fill(1);for(let t=0;t<k;t++)for(let i=1;i<n;i++)a[i]=(a[i]+a[i-1])%1000000007;return a[n-1];}
module.exports = solve;
