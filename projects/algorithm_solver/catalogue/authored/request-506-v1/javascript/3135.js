// Original candidate. Contract: https://leetcode.com/problems/equalize-strings-by-adding-or-removing-characters-at-ends/
"use strict";
function solve(initial,target){const d=Array(target.length+1).fill(0);let best=0;for(const a of initial){let previous=0;for(let j=1;j<=target.length;j++){const old=d[j];d[j]=a===target[j-1]?previous+1:0;previous=old;best=Math.max(best,d[j]);}}return initial.length+target.length-2*best;}
module.exports = solve;
