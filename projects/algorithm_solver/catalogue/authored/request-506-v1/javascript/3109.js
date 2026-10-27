// Original candidate. Contract: https://leetcode.com/problems/find-the-index-of-permutation/
"use strict";
function solve(perm){const n=perm.length,M=1000000007,f=Array(n+1).fill(1),b=Array.from({length:n+1},(_,i)=>i&-i);for(let i=1;i<=n;i++)f[i]=f[i-1]*i%M;let a=0;for(let i=0;i<n;i++){let j=perm[i]-1,s=0;while(j){s+=b[j];j-=j&-j;}a=(a+s*f[n-i-1])%M;j=perm[i];while(j<=n){b[j]--;j+=j&-j;}}return a;}
module.exports = solve;
