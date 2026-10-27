/* Original candidate for LeetCode 2467. Contract: https://leetcode.com/problems/most-profitable-path-in-a-tree/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time and space; iterative traversal avoids deep recursion */
"use strict";
function solve(edges,bob,amount){let n=amount.length,adj=Array.from({length:n},()=>[]);for(const [u,v] of edges){adj[u].push(v);adj[v].push(u);}let parent=Array(n).fill(-1),depth=Array(n).fill(0),order=[0];for(let h=0;h<order.length;h++){let u=order[h];for(const v of adj[u])if(v!==parent[u]){parent[v]=u;depth[v]=depth[u]+1;order.push(v);}}let bt=Array(n).fill(n+1),t=0;while(bob!==-1){bt[bob]=t++;bob=parent[bob];}let income=Array(n).fill(0),answer=-Infinity;for(const u of order){let value=depth[u]<bt[u]?amount[u]:depth[u]===bt[u]?amount[u]/2:0;income[u]=(parent[u]===-1?0:income[parent[u]])+value;if(u&&adj[u].length===1)answer=Math.max(answer,income[u]);}return answer;}
module.exports = solve;
