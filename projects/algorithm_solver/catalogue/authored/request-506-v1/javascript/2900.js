// Original implementation. Contract: https://leetcode.com/problems/longest-unequal-adjacent-groups-subsequence-i/
"use strict";
function solve(words,groups){let last=-1;const out=[];for(let i=0;i<words.length;i++)if(groups[i]!==last){out.push(words[i]);last=groups[i];}return out;}
module.exports = solve;
