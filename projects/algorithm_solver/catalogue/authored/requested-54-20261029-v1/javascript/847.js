"use strict";
function solve(graph){const n=graph.length,q=[],seen=new Set();
 for(let i=0;i<n;i++){q.push([i,1<<i,0]);seen.add((1<<i)*n+i);}
 for(let h=0;h<q.length;h++){const [u,mask,d]=q[h];if(mask===(1<<n)-1)return d;
  for(const v of graph[u]){const m=mask|(1<<v),key=m*n+v;if(!seen.has(key)){seen.add(key);q.push([v,m,d+1]);}}
 }
}

function shortestPathLength(graph) { return solve(graph); }
module.exports=solve;
module.exports.shortestPathLength=shortestPathLength;
