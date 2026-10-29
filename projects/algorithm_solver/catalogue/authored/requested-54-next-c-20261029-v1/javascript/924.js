"use strict";
function solve(graph,initial){const n=graph.length,label=Array(n).fill(-1),sizes=[];for(let start=0;start<n;start++){if(label[start]>=0)continue;const id=sizes.length,stack=[start];label[start]=id;let count=0;while(stack.length){const u=stack.pop();count++;for(let v=0;v<n;v++)if(graph[u][v]&&label[v]<0){label[v]=id;stack.push(v);}}sizes.push(count);}
 const seeds=Array(sizes.length).fill(0);for(const x of initial)seeds[label[x]]++;let best=-1,saved=-1;for(const x of initial){const gain=seeds[label[x]]===1?sizes[label[x]]:0;if(gain>saved||gain===saved&&x<best){best=x;saved=gain;}}return best;
}

function minMalwareSpread(graph, initial) { return solve(graph, initial); }
module.exports=solve;module.exports.minMalwareSpread=minMalwareSpread;
