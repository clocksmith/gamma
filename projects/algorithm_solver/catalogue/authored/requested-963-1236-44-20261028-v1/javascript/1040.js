"use strict";
function solve(stones){const a=[...stones].sort((a,b)=>a-b),n=a.length,maximum=Math.max(a[n-1]-a[1],a[n-2]-a[0])-(n-2);let minimum=n,left=0;for(let right=0;right<n;right++){while(a[right]-a[left]+1>n)left++;const size=right-left+1,candidate=size===n-1&&a[right]-a[left]===n-2?2:n-size;minimum=Math.min(minimum,candidate);}return [minimum,maximum];}

function numMovesStonesII(stones){return solve(stones);}
module.exports=solve;
module.exports.numMovesStonesII=numMovesStonesII;
