// Original candidate. Contract: https://leetcode.com/problems/number-of-self-divisible-permutations/
"use strict";
function solve(n){const dp=Array(1<<n).fill(0);dp[0]=1;function gcd(a,b){while(b)[a,b]=[b,a%b];return a;}for(let m=0;m<dp.length;m++){let p=1,t=m;while(t){t&=t-1;p++;}for(let j=0;j<n;j++)if(!(m>>j&1)&&gcd(j+1,p)===1)dp[m|1<<j]+=dp[m];}return dp[dp.length-1];}
module.exports = solve;
