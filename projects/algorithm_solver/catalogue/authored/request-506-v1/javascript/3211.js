/* Original candidate for LeetCode 3211. Contract: https://leetcode.com/problems/generate-binary-strings-without-adjacent-zeros/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n*F(n)) output time and space; output lexical order, any order allowed */
"use strict";
function solve(n){let out=[''];for(let i=0;i<n;i++){let next=[];for(const s of out){if(!s.endsWith('0'))next.push(s+'0');next.push(s+'1');}out=next;}return out;}
module.exports = solve;
