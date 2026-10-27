/* Original candidate for LeetCode 2445. Contract: https://leetcode.com/problems/number-of-nodes-with-value-one/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n+q) time, O(n) space */
"use strict";
function solve(n,queries){let a=new Uint8Array(n+1);for(const q of queries)a[q]^=1;let ans=0;for(let i=1;i<=n;i++){a[i]^=a[Math.floor(i/2)];ans+=a[i];}return ans;}
module.exports = solve;
