// Original implementation. Contract: https://leetcode.com/problems/count-the-number-of-special-characters-ii/
"use strict";
function solve(word){const lo=Array(26).fill(-1),hi=Array(26).fill(Infinity);for(let i=0;i<word.length;i++){let c=word.charCodeAt(i);if(c>=97)lo[c-97]=i;else hi[c-65]=Math.min(hi[c-65],i);}return lo.reduce((s,x,i)=>s+(x>=0&&hi[i]<Infinity&&x<hi[i]),0);}
module.exports = solve;
