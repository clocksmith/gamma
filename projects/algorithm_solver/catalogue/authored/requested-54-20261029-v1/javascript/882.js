"use strict";
function solve(edges,maxMoves,n){const graph=Array.from({length:n},()=>[]),dist=Array(n).fill(Infinity),used=Array(n).fill(false);dist[0]=0;
 for(const [u,v,c] of edges){graph[u].push([v,c+1]);graph[v].push([u,c+1]);}
 for(let step=0;step<n;step++){let u=-1;for(let i=0;i<n;i++)if(!used[i]&&(u<0||dist[i]<dist[u]))u=i;if(u<0||dist[u]>maxMoves)break;used[u]=true;for(const [v,w] of graph[u])dist[v]=Math.min(dist[v],dist[u]+w);}
 let ans=dist.filter(d=>d<=maxMoves).length;for(const [u,v,c] of edges)ans+=Math.min(c,Math.max(0,maxMoves-dist[u])+Math.max(0,maxMoves-dist[v]));return ans;
}

function reachableNodes(edges, maxMoves, n) { return solve(edges, maxMoves, n); }
module.exports=solve;
module.exports.reachableNodes=reachableNodes;
