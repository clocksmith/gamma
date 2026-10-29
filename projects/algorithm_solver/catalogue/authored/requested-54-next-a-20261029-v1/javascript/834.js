"use strict";
function solve(n,edges){const graph=Array.from({length:n},()=>[]);for(const [a,b] of edges){graph[a].push(b);graph[b].push(a);}const parent=Array(n).fill(-1),order=[0];
 for(let h=0;h<order.length;h++){const u=order[h];for(const v of graph[u])if(v!==parent[u]){parent[v]=u;order.push(v);}}
 const size=Array(n).fill(1),answer=Array(n).fill(0);for(let i=order.length-1;i>0;i--){const u=order[i],p=parent[u];size[p]+=size[u];answer[p]+=answer[u]+size[u];}
 for(let i=1;i<order.length;i++){const u=order[i];answer[u]=answer[parent[u]]+n-2*size[u];}return answer;
}

function sumOfDistancesInTree(n, edges) { return solve(n, edges); }
module.exports=solve;
module.exports.sumOfDistancesInTree=sumOfDistancesInTree;
