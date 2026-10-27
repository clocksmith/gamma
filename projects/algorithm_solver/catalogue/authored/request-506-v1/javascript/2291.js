/* Original candidate for LeetCode 2291. Contract: https://leetcode.com/problems/maximum-profit-from-trading-stocks/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n budget) time, O(budget) space */
"use strict";
function solve(present,future,budget){let dp=Array(budget+1).fill(0);for(let i=0;i<present.length;i++){const p=present[i],v=future[i]-p;if(v>0)for(let b=budget;b>=p;b--)dp[b]=Math.max(dp[b],dp[b-p]+v);}return dp[budget];}
module.exports = solve;
