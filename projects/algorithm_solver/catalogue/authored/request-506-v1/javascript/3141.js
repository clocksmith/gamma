// Original candidate implementation. Contract: https://leetcode.com/problems/maximum-hamming-distances/
"use strict";
function solve(nums,m){const size=1<<m,dist=new Int32Array(size).fill(-1),q=[];for(const v of nums)if(dist[v]<0){dist[v]=0;q.push(v);}for(let h=0;h<q.length;h++){const v=q[h];for(let b=0;b<m;b++){const w=v^(1<<b);if(dist[w]<0){dist[w]=dist[v]+1;q.push(w);}}}return nums.map(v=>m-dist[(size-1)^v]);}
module.exports = solve;
