/* Original candidate for LeetCode 2730. Contract: https://leetcode.com/problems/find-the-longest-semi-repetitive-substring/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space */
"use strict";
function solve(s){let left=0,pairs=0,ans=0;for(let right=0;right<s.length;right++){if(right&&s[right]===s[right-1])pairs++;while(pairs>1){if(s[left]===s[left+1])pairs--;left++;}ans=Math.max(ans,right-left+1);}return ans;}
module.exports = solve;
