// Original candidate implementation. Contract: https://leetcode.com/problems/count-pairs-of-points-with-distance-k/
"use strict";
function solve(coordinates,k){const seen=new Map();let result=0;for(const [x,y] of coordinates){for(let d=0;d<=k;d++)result+=seen.get((x^d)+','+(y^(k-d)))||0;const key=x+','+y;seen.set(key,(seen.get(key)||0)+1);}return result;}
module.exports = solve;
