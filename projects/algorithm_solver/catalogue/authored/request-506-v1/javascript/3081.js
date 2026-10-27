/* Original candidate for LeetCode 3081. Contract: https://leetcode.com/problems/replace-question-marks-in-string-to-minimize-its-value/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n) time, O(n) space */
"use strict";
function solve(s){let counts=Array(26).fill(0),added=[];for(const c of s)if(c!=='?')counts[c.charCodeAt(0)-97]++;for(const c of s)if(c==='?'){let j=0;for(let k=1;k<26;k++)if(counts[k]<counts[j])j=k;counts[j]++;added.push(String.fromCharCode(97+j));}added.sort();let i=0;return [...s].map(c=>c==='?'?added[i++]:c).join('');}
module.exports = solve;
