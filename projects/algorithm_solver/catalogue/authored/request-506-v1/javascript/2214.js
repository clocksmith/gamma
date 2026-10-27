// Original implementation. Contract: https://leetcode.com/problems/minimum-health-to-beat-game/
"use strict";
function solve(damage,armor){let sum=0,mx=0;for(const x of damage){sum+=x;mx=Math.max(mx,x);}return sum-Math.min(mx,armor)+1;}
module.exports = solve;
