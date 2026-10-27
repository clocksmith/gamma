// Original candidate. Contract: https://leetcode.com/problems/find-if-path-exists-in-graph/
"use strict";
function solve(n, edges, source, destination) {
 const p=Array.from({length:n},(_,i)=>i),z=Array(n).fill(1);
 function find(x){while(x!==p[x]){p[x]=p[p[x]];x=p[x];}return x;}
 for(let [a,b] of edges){a=find(a);b=find(b);if(a!==b){if(z[a]<z[b])[a,b]=[b,a];p[b]=a;z[a]+=z[b];}}
 return find(source)===find(destination);
}
module.exports = solve;
