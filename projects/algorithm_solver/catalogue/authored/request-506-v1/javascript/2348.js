// Original candidate implementation. Contract: https://leetcode.com/problems/number-of-zero-filled-subarrays/
"use strict";
function solve(nums){let answer=0,run=0;for(const v of nums){run=v===0?run+1:0;answer+=run;}return answer;}
module.exports = solve;
