// Original implementation. Contract: https://leetcode.com/problems/number-of-employees-who-met-the-target/
"use strict";
function solve(hours,target){return hours.reduce((s,x)=>s+(x>=target),0);}
module.exports = solve;
