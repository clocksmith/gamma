"use strict";
function solve(n,k){const mod=1000000007;let previous=new Array(k+1).fill(0);previous[0]=1;for(let len=1;len<=n;len++){const cur=new Array(k+1).fill(0);let window=0;for(let inv=0;inv<=k;inv++){window+=previous[inv];if(inv>=len)window-=previous[inv-len];window=(window%mod+mod)%mod;cur[inv]=window;}previous=cur;}return previous[k];}

function kInversePairs(n, k){return solve(n, k);}
module.exports=solve;
module.exports.kInversePairs=kInversePairs;
