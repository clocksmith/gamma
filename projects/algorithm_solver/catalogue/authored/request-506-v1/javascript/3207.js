// Original candidate. Contract: https://leetcode.com/problems/maximum-points-after-enemy-battles/
"use strict";
function solve(enemyEnergies,currentEnergy){let smallest=Infinity,total=0;for(const x of enemyEnergies){smallest=Math.min(smallest,x);total+=x;}return currentEnergy<smallest?0:Math.floor((currentEnergy+total-smallest)/smallest);}
module.exports = solve;
