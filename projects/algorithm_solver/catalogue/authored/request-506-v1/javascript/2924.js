/* Original candidate for LeetCode 2924. Contract: https://leetcode.com/problems/find-champion-ii/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n+m) time, O(n) space; input is a DAG */
"use strict";
function solve(n,edges){let indegree=Array(n).fill(0);for(const [u,v] of edges)indegree[v]++;let roots=[];for(let i=0;i<n;i++)if(!indegree[i])roots.push(i);return roots.length===1?roots[0]:-1;}
module.exports = solve;
