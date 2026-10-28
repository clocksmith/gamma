"use strict";
function solve(n, edges, x, y, z) {
const adjacency=Array.from({length:n},()=>[]);for(const [a,b] of edges){adjacency[a].push(b);adjacency[b].push(a);}function distances(start){const result=new Int32Array(n).fill(-1),queue=[start];result[start]=0;for(let head=0;head<queue.length;head++){const node=queue[head];for(const other of adjacency[node])if(result[other]===-1){result[other]=result[node]+1;queue.push(other);}}return result;}const dx=distances(x),dy=distances(y),dz=distances(z);let answer=0;for(let i=0;i<n;i++){const values=[dx[i],dy[i],dz[i]].sort((a,b)=>a-b);if(Math.imul(values[0],values[0])+Math.imul(values[1],values[1])===Math.imul(values[2],values[2]))answer++;}return answer;
}
function specialNodes(n, edges, x, y, z) { return solve(n, edges, x, y, z); }
module.exports=solve;
module.exports.specialNodes=specialNodes;
