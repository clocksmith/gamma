/* Original candidate for LeetCode 3137. Contract: https://leetcode.com/problems/minimum-number-of-operations-to-make-word-k-periodic/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) expected time and space */
"use strict";
function solve(word,k){let counts=new Map(),best=0;for(let i=0;i<word.length;i+=k){let key=word.slice(i,i+k),n=(counts.get(key)||0)+1;counts.set(key,n);best=Math.max(best,n);}return word.length/k-best;}
module.exports = solve;
