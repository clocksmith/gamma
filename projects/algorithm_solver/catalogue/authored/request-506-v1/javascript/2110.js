// Original candidate implementation. Contract: https://leetcode.com/problems/number-of-smooth-descent-periods-of-a-stock/
"use strict";
function solve(prices){let result=0,run=0;for(let i=0;i<prices.length;i++){run=i&&prices[i-1]===prices[i]+1?run+1:1;result+=run;}return result;}
module.exports = solve;
