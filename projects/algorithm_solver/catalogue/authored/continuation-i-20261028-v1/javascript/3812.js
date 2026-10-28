function solve(n,edges,start,target){const graph=Array.from({length:n},()=>[]);for(let i=0;i<edges.length;i++){const [u,v]=edges[i];graph[u].push([v,i]);graph[v].push([u,i]);}const parent=Array(n).fill(-1),parentEdge=Array(n).fill(-1),order=[0];parent[0]=0;for(let t=0;t<order.length;t++){const u=order[t];for(const [v,edge] of graph[u])if(v!==parent[u]){parent[v]=u;parentEdge[v]=edge;order.push(v);}}const mismatch=Array.from({length:n},(_,i)=>Number(start[i]!==target[i])),chosen=Array(n-1).fill(false);for(let t=order.length-1;t>0;t--){const v=order[t];if(mismatch[v]){chosen[parentEdge[v]]=true;mismatch[parent[v]]^=1;}}if(mismatch[0])return[-1];const answer=[];for(let i=0;i<chosen.length;i++)if(chosen[i])answer.push(i);return answer;}

var minimumFlips = solve;
module.exports = solve;
