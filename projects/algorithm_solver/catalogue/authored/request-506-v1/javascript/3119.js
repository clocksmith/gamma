/* Original candidate for LeetCode 3119. Contract: https://leetcode.com/problems/maximum-number-of-potholes-that-can-be-fixed/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n) time, O(n) space */
"use strict";
function solve(road,budget){let runs=road.split('.').filter(Boolean).map(s=>s.length).sort((a,b)=>b-a),ans=0;for(const r of runs){let t=Math.min(r,Math.max(0,budget-1));ans+=t;budget-=t+1;if(budget<=1)break;}return ans;}
module.exports = solve;
