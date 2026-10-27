// Original implementation. Contract: https://leetcode.com/problems/maximum-increasing-triplet-value/
"use strict";
function solve(a){const values=[...new Set(a)].sort((a,b)=>a-b),ranks=new Map(values.map((x,i)=>[x,i+1])),bit=Array(values.length+1).fill(0),suffix=Array(a.length+1).fill(0);for(let i=a.length-1;i>=0;i--)suffix[i]=Math.max(suffix[i+1],a[i]);let answer=0;for(let j=0;j<a.length;j++){const x=a[j],rank=ranks.get(x);let best=0;for(let i=rank-1;i;i-=i&-i)best=Math.max(best,bit[i]);if(best&&suffix[j+1]>x)answer=Math.max(answer,best-x+suffix[j+1]);for(let i=rank;i<bit.length;i+=i&-i)bit[i]=Math.max(bit[i],x);}return answer;}
module.exports = solve;
