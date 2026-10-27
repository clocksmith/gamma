// Original candidate implementation. Contract: https://leetcode.com/problems/find-the-first-player-to-win-k-games-in-a-row/
"use strict";
function solve(skills,k){let champion=0,wins=0;for(let i=1;i<skills.length;i++){if(skills[i]>skills[champion]){champion=i;wins=0;}if(++wins>=k)return champion;}return champion;}
module.exports = solve;
