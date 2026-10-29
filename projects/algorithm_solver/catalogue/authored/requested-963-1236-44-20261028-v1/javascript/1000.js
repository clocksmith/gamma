"use strict";
function solve(stones,k){const n=stones.length;if((n-1)%(k-1))return -1;const p=[0];for(const v of stones)p.push(p[p.length-1]+v);const dp=Array.from({length:n},()=>new Array(n).fill(0));for(let len=k;len<=n;len++)for(let l=0;l+len<=n;l++){const r=l+len-1;let best=Infinity;for(let m=l;m<r;m+=k-1)best=Math.min(best,dp[l][m]+dp[m+1][r]);dp[l][r]=best+((len-1)%(k-1)===0?p[r+1]-p[l]:0);}return dp[0][n-1];}

function mergeStones(stones, k){return solve(stones, k);}
module.exports=solve;
module.exports.mergeStones=mergeStones;
