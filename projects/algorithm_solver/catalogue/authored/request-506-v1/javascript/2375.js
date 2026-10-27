/* Original candidate for LeetCode 2375. Contract: https://leetcode.com/problems/construct-smallest-number-from-di-string/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time and space */
"use strict";
function solve(pattern){let out=[],stack=[];for(let i=0;i<=pattern.length;i++){stack.push(String(i+1));if(i===pattern.length||pattern[i]==='I'){while(stack.length)out.push(stack.pop());}}return out.join('');}
module.exports = solve;
