/* Original candidate for LeetCode 2102. Contract: https://leetcode.com/problems/sequentially-ordinal-rank-tracker/
Development tests only; not admitted or independently qualified.
Batch class-call adapter. Coordinate compression sees future names but only past additions affect returned ranks; not a streaming class API.
Complexity: O(q log q) time, O(q) space */
"use strict";
function solve(operations,args){const ranked=[];for(let i=0;i<operations.length;i++)if(operations[i]==='add')ranked.push([-args[i][1],args[i][0]]);ranked.sort((a,b)=>a[0]-b[0]||(a[1]<b[1]?-1:a[1]>b[1]?1:0));let rank=new Map(ranked.map((a,i)=>[a[1],i+1])),bit=Array(ranked.length+1).fill(0),out=[],query=0;for(let t=0;t<operations.length;t++){const op=operations[t],a=args[t];if(op==='add'){for(let i=rank.get(a[0]);i<bit.length;i+=i&-i)bit[i]++;out.push(null);}else if(op==='get'){let k=++query,i=0,step=1;while(step*2<=ranked.length)step*=2;for(;step;step=Math.floor(step/2)){let j=i+step;if(j<bit.length&&bit[j]<k){k-=bit[j];i=j;}}out.push(ranked[i][1]);}else out.push(null);}return out;}
module.exports = solve;
