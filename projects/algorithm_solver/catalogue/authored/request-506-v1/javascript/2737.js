// Original implementation. Contract: https://leetcode.com/problems/find-the-closest-marked-node/
"use strict";
function solve(n,edges,s,marked){const g=Array.from({length:n},()=>[]);for(const [u,v,w] of edges)g[u].push([v,w]);const d=Array(n).fill(Infinity),used=Array(n).fill(false),targets=new Set(marked);d[s]=0;for(let z=0;z<n;z++){let u=-1;for(let i=0;i<n;i++)if(!used[i]&&(u<0||d[i]<d[u]))u=i;if(u<0||d[u]===Infinity)return -1;if(targets.has(u))return d[u];used[u]=true;for(const [v,w] of g[u])d[v]=Math.min(d[v],d[u]+w);}return -1;}
module.exports = solve;
