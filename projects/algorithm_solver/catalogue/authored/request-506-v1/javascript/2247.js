/* Original candidate for LeetCode 2247. Contract: https://leetcode.com/problems/maximum-cost-of-trip-with-k-highways/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(2^n n²) time, O(2^n n) space */
"use strict";
function solve(n,highways,k){if(k>=n)return -1;const g=Array.from({length:n},()=>[]);for(const[a,b,w]of highways){g[a].push([b,w]);g[b].push([a,w]);}let dp=new Map(Array.from({length:n},(_,i)=>[((1<<i)*n+i),0]));for(let t=0;t<k;t++){let nd=new Map();for(const[key,c]of dp){const u=key%n,mask=Math.floor(key/n);for(const[v,w]of g[u])if(!(mask&(1<<v))){const z=(mask|(1<<v))*n+v;nd.set(z,Math.max(nd.get(z)??-1,c+w));}}dp=nd;}let ans=-1;for(const v of dp.values())ans=Math.max(ans,v);return ans;}
module.exports = solve;
