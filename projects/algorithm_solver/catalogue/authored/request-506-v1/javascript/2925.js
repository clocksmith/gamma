// Original implementation. Contract: https://leetcode.com/problems/maximum-score-after-applying-operations-on-a-tree/
"use strict";
function solve(edges,values){const n=values.length,g=Array.from({length:n},()=>[]);for(const [u,v] of edges){g[u].push(v);g[v].push(u);}const parent=Array(n).fill(-1),order=[0];for(let h=0;h<order.length;h++){const u=order[h];for(const v of g[u])if(v!==parent[u]){parent[v]=u;order.push(v);}}const keep=Array(n).fill(0);for(let i=order.length-1;i>=0;i--){const u=order[i];let sum=0,children=0;for(const v of g[u])if(v!==parent[u]){sum+=keep[v];children++;}keep[u]=children?Math.min(values[u],sum):values[u];}return values.reduce((s,x)=>s+x,0)-keep[0];}
module.exports = solve;
