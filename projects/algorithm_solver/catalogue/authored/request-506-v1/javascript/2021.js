// Original implementation. Contract: https://leetcode.com/problems/brightest-position-on-street/
"use strict";
function solve(lights){const delta=new Map();for(const [x,r] of lights){delta.set(x-r,(delta.get(x-r)||0)+1);delta.set(x+r+1,(delta.get(x+r+1)||0)-1);}let best=-1,active=0,out=0;for(const x of [...delta.keys()].sort((a,b)=>a-b)){active+=delta.get(x);if(active>best){best=active;out=x;}}return out;}
module.exports = solve;
