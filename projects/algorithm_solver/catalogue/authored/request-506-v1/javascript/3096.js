// Original candidate. Contract: https://leetcode.com/problems/minimum-levels-to-gain-more-points/
"use strict";
function solve(possible){let total=possible.reduce((s,x)=>s+2*x-1,0),p=0;for(let i=0;i<possible.length-1;i++){p+=2*possible[i]-1;if(2*p>total)return i+1;}return -1;}
module.exports = solve;
