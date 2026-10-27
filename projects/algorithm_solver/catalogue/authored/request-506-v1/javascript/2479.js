/* Original candidate for LeetCode 2479. Contract: https://leetcode.com/problems/maximum-xor-of-two-non-overlapping-subtrees/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log S) time and space, S=sum(values); 46-bit arithmetic uses exact Number division, not 32-bit JS XOR */
"use strict";
function solve(n,edges,values){let g=Array.from({length:n},()=>[]);for(const[a,b]of edges){g[a].push(b);g[b].push(a);}let par=Array(n).fill(-1),order=[0],sums=values.slice();for(let i=0;i<order.length;i++){let u=order[i];for(const v of g[u])if(v!==par[u]){par[v]=u;order.push(v);}}for(let i=n-1;i>0;i--){let u=order[i];sums[par[u]]+=sums[u];}let trie={},ans=0,stack=[[0,false]],powers=Array.from({length:46},(_,i)=>2**i);while(stack.length){let[u,exit]=stack.pop(),x=sums[u];if(exit){let node=trie;for(let b=45;b>=0;b--){let bit=Math.floor(x/powers[b])%2;node=node[bit]??=( {} );}}else{if(Object.keys(trie).length){let node=trie,v=0;for(let b=45;b>=0;b--){let bit=Math.floor(x/powers[b])%2;if(node[1-bit]){v+=powers[b];node=node[1-bit];}else node=node[bit];}ans=Math.max(ans,v);}stack.push([u,true]);for(const v of g[u])if(v!==par[u])stack.push([v,false]);}}return ans;}
module.exports = solve;
