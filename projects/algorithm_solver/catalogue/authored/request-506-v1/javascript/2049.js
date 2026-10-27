// Original candidate implementation. Contract: https://leetcode.com/problems/count-nodes-with-the-highest-score/
"use strict";
function solve(parents){const n=parents.length,ch=Array.from({length:n},()=>[]);for(let i=1;i<n;i++)ch[parents[i]].push(i);const order=[0],size=Array(n).fill(1);for(let i=0;i<order.length;i++)for(const v of ch[order[i]])order.push(v);let best=0n,count=0;for(let i=n-1;i>=0;i--){const u=order[i];let p=1n;for(const v of ch[u]){size[u]+=size[v];p*=BigInt(size[v]);}if(n>size[u])p*=BigInt(n-size[u]);if(p>best){best=p;count=1;}else if(p===best)count++;}return count;}
module.exports = solve;
