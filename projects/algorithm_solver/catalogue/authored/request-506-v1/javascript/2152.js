// Original implementation. Contract: https://leetcode.com/problems/minimum-number-of-lines-to-cover-points/
"use strict";
function solve(p){const n=p.length,m=Array.from({length:n},()=>Array(n).fill(0));for(let i=0;i<n;i++)for(let j=0;j<n;j++)if(i!==j)for(let k=0;k<n;k++)if((p[k][0]-p[i][0])*(p[j][1]-p[i][1])===(p[k][1]-p[i][1])*(p[j][0]-p[i][0]))m[i][j]|=1<<k;const memo=new Map([[0,0]]);function dp(mask){if(memo.has(mask))return memo.get(mask);let i=0;while(!(mask>>i&1))i++;let best=1+dp(mask^(1<<i));for(let j=i+1;j<n;j++)if(mask>>j&1)best=Math.min(best,1+dp(mask&~m[i][j]));memo.set(mask,best);return best;}return dp((1<<n)-1);}
module.exports = solve;
