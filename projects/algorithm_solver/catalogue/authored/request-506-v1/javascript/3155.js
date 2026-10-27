// Original candidate. Contract: https://leetcode.com/problems/maximum-number-of-upgradable-servers/
"use strict";
function solve(count,upgrade,sell,money){return count.map((c,i)=>Math.min(c,Math.floor((money[i]+c*sell[i])/(upgrade[i]+sell[i]))));}
module.exports = solve;
