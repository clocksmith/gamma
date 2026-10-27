// Original implementation. Contract: https://leetcode.com/problems/first-day-where-you-have-been-in-all-the-rooms/
"use strict";
function solve(nextVisit){const d=Array(nextVisit.length).fill(0),M=1000000007;for(let i=1;i<d.length;i++)d[i]=(2*d[i-1]-d[nextVisit[i-1]]+2+M)%M;return d.at(-1);}
module.exports = solve;
