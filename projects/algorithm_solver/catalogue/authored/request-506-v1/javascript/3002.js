// Original implementation. Contract: https://leetcode.com/problems/maximum-size-of-a-set-after-removals/
"use strict";
function solve(a,b){const x=new Set(a),y=new Set(b),union=new Set([...x,...y]),h=a.length/2;return Math.min(union.size,Math.min(x.size,h)+Math.min(y.size,h));}
module.exports = solve;
