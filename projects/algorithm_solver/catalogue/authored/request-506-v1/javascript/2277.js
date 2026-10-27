// Original implementation. Contract: https://leetcode.com/problems/closest-node-to-path-in-tree/
"use strict";
function solve(n,edges,query){const g=Array.from({length:n},()=>[]);for(const [u,v] of edges){g[u].push(v);g[v].push(u);}const d=[];for(let s=0;s<n;s++){const row=Array(n).fill(-1),q=[s];row[s]=0;for(let h=0;h<q.length;h++)for(const v of g[q[h]])if(row[v]<0){row[v]=row[q[h]]+1;q.push(v);}d.push(row);}return query.map(([s,t,x])=>{let best=-1;for(let v=0;v<n;v++)if(d[s][v]+d[v][t]===d[s][t]&&(best<0||d[x][v]<d[x][best]))best=v;return best;});}
module.exports = solve;
