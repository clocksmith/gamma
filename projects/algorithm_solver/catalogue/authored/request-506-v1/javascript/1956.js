/* Original candidate for LeetCode 1956. Contract: https://leetcode.com/problems/minimum-time-for-k-virus-variants-to-spread/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(A n log n) time, O(n) space; A <= 10000 candidate lattice centers */
"use strict";
function solve(points,k){let best=Infinity;let xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);for(let x=Math.min(...xs);x<=Math.max(...xs);x++)for(let y=Math.min(...ys);y<=Math.max(...ys);y++){let d=points.map(([a,b])=>Math.abs(x-a)+Math.abs(y-b)).sort((a,b)=>a-b);best=Math.min(best,d[k-1]);}return best;}
module.exports = solve;
