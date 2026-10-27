/* Original candidate for LeetCode 2957. Contract: https://leetcode.com/problems/remove-adjacent-almost-equal-characters/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space */
"use strict";
function solve(word){let i=1,ans=0;while(i<word.length){if(Math.abs(word.charCodeAt(i)-word.charCodeAt(i-1))<=1){ans++;i+=2;}else i++;}return ans;}
module.exports = solve;
