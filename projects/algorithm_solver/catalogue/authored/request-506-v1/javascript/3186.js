/* Original candidate for LeetCode 3186. Contract: https://leetcode.com/problems/maximum-total-damage-with-spell-casting/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n) time, O(n) space; sum <= 10^14, exact in JS Number */
"use strict";
function solve(power){let counts=new Map();for(const x of power)counts.set(x,(counts.get(x)||0)+1);let values=[...counts.keys()].sort((a,b)=>a-b),dp=[0],j=0;for(let i=0;i<values.length;i++){let x=values[i];while(j<i&&values[j]<x-2)j++;dp.push(Math.max(dp[dp.length-1],dp[j]+x*counts.get(x)));}return dp[dp.length-1];}
module.exports = solve;
