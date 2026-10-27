// Original candidate implementation. Contract: https://leetcode.com/problems/distance-to-a-cycle-in-undirected-graph/
"use strict";
function solve(n,edges){const adj=Array.from({length:n},()=>[]);for(const [a,b] of edges){adj[a].push(b);adj[b].push(a);}const degree=adj.map(a=>a.length),q=[];for(let i=0;i<n;i++)if(degree[i]===1)q.push(i);for(let h=0;h<q.length;h++){const v=q[h];degree[v]=0;for(const w of adj[v])if(degree[w]>0&&--degree[w]===1)q.push(w);}const d=degree.map(v=>v>0?0:-1),b=[];for(let i=0;i<n;i++)if(d[i]===0)b.push(i);for(let h=0;h<b.length;h++)for(const w of adj[b[h]])if(d[w]<0){d[w]=d[b[h]]+1;b.push(w);}return d;}
module.exports = solve;
