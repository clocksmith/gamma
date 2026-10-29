"use strict";
function solve(k,n){const reachable=Array(k+1).fill(0);let moves=0;while(reachable[k]<n){moves++;for(let eggs=k;eggs>0;eggs--)reachable[eggs]=Math.min(n,reachable[eggs]+reachable[eggs-1]+1);}return moves;}
function superEggDrop(k,n){return solve(k,n);}
module.exports=solve;module.exports.superEggDrop=superEggDrop;
