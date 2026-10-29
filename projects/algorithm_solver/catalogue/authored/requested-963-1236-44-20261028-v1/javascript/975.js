"use strict";
function solve(arr){const n=arr.length;function next(order){const result=new Array(n).fill(-1),stack=[];for(const i of order){while(stack.length&&stack[stack.length-1]<i)result[stack.pop()]=i;stack.push(i);}return result;}const ids=arr.map((_,i)=>i),hi=next([...ids].sort((a,b)=>arr[a]-arr[b]||a-b)),lo=next([...ids].sort((a,b)=>arr[b]-arr[a]||a-b)),odd=new Array(n).fill(false),even=new Array(n).fill(false);odd[n-1]=even[n-1]=true;for(let i=n-2;i>=0;i--){if(hi[i]>=0)odd[i]=even[hi[i]];if(lo[i]>=0)even[i]=odd[lo[i]];}return odd.reduce((a,b)=>a+Number(b),0);}

function oddEvenJumps(arr){return solve(arr);}
module.exports=solve;
module.exports.oddEvenJumps=oddEvenJumps;
