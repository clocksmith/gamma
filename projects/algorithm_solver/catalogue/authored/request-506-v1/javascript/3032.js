/* Original candidate for LeetCode 3032. Contract: https://leetcode.com/problems/count-numbers-with-unique-digits-ii/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O((b-a+1) log b) time, O(log b) space */
"use strict";
function solve(a,b){let ans=0;for(let x=a;x<=b;x++){let s=String(x);if(new Set(s).size===s.length)ans++;}return ans;}
module.exports = solve;
