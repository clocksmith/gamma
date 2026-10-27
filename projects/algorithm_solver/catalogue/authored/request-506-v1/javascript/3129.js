// Original implementation. Contract: https://leetcode.com/problems/find-all-possible-stable-binary-arrays-i/
"use strict";
function solve(zero,one,limit){const M=1000000007,a=Array.from({length:zero+1},()=>Array(one+1).fill(0)),b=Array.from({length:zero+1},()=>Array(one+1).fill(0));for(let i=1;i<=Math.min(zero,limit);i++)a[i][0]=1;for(let j=1;j<=Math.min(one,limit);j++)b[0][j]=1;for(let i=1;i<=zero;i++)for(let j=1;j<=one;j++){a[i][j]=(a[i-1][j]+b[i-1][j]-(i>limit?b[i-limit-1][j]:0)+M)%M;b[i][j]=(a[i][j-1]+b[i][j-1]-(j>limit?a[i][j-limit-1]:0)+M)%M;}return (a[zero][one]+b[zero][one])%M;}
module.exports = solve;
