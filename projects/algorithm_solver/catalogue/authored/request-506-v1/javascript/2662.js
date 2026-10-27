// Original candidate. Contract: https://leetcode.com/problems/minimum-cost-of-a-path-with-special-roads/
"use strict";
function solve(start,target,roads){const n=roads.length,d=roads.map(r=>Math.abs(start[0]-r[0])+Math.abs(start[1]-r[1])+r[4]),used=Array(n).fill(false);let ans=Math.abs(start[0]-target[0])+Math.abs(start[1]-target[1]);for(let k=0;k<n;k++){let u=-1;for(let j=0;j<n;j++)if(!used[j]&&(u<0||d[j]<d[u]))u=j;used[u]=true;const x=roads[u][2],y=roads[u][3];ans=Math.min(ans,d[u]+Math.abs(x-target[0])+Math.abs(y-target[1]));for(let v=0;v<n;v++){const r=roads[v];d[v]=Math.min(d[v],d[u]+Math.abs(x-r[0])+Math.abs(y-r[1])+r[4]);}}return ans;}
module.exports = solve;
