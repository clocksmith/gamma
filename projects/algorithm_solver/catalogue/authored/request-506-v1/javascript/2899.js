/* Original candidate for LeetCode 2899. Contract: https://leetcode.com/problems/last-visited-integers/
Development tests only; not admitted or independently qualified.
Current official contract takes positive integers and -1, not historical string words.
Complexity: O(n) time and space */
"use strict";
function solve(nums){let seen=[],ans=[],k=0;for(const x of nums){if(x===-1){k++;ans.push(k<=seen.length?seen[seen.length-k]:-1);}else{seen.push(x);k=0;}}return ans;}
module.exports = solve;
