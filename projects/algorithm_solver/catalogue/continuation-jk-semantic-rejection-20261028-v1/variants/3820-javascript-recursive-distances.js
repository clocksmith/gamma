"use strict";
function solve(n, edges, x, y, z) {
const adjacency=Array.from({length:n},()=>[]);for(const [a,b] of edges){adjacency[a].push(b);adjacency[b].push(a);}function distances(start){const result=new Int32Array(n).fill(-1);result[start]=0;(function visit(node){for(const other of adjacency[node])if(result[other]===-1){result[other]=result[node]+1;visit(other);}})(start);return result;}const dx=distances(x),dy=distances(y),dz=distances(z);let answer=0;for(let i=0;i<n;i++){const values=[dx[i],dy[i],dz[i]].sort((a,b)=>a-b);if(values[0]**2+values[1]**2===values[2]**2)answer++;}return answer;
}
function specialNodes(n, edges, x, y, z) { return solve(n, edges, x, y, z); }
module.exports=solve;
module.exports.specialNodes=specialNodes;
