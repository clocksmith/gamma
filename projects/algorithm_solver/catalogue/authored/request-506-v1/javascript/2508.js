/* Original candidate for LeetCode 2508. Contract: https://leetcode.com/problems/add-edges-to-make-degrees-of-all-nodes-even/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n+m) expected time and space */
"use strict";
function solve(n,edges){let adj=Array.from({length:n+1},()=>new Set());for(const [u,v] of edges){adj[u].add(v);adj[v].add(u);}let odd=[];for(let i=1;i<=n;i++)if(adj[i].size%2)odd.push(i);if(!odd.length)return true;if(odd.length===2){let [a,b]=odd;if(!adj[a].has(b))return true;for(let i=1;i<=n;i++)if(i!==a&&i!==b&&!adj[a].has(i)&&!adj[b].has(i))return true;}if(odd.length===4){let [a,b,c,d]=odd;return (!adj[a].has(b)&&!adj[c].has(d))||(!adj[a].has(c)&&!adj[b].has(d))||(!adj[a].has(d)&&!adj[b].has(c));}return false;}
module.exports = solve;
