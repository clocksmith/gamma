// Original candidate implementation. Contract: https://leetcode.com/problems/distribute-candies-among-children-iii/
"use strict";
function solve(n,limit){const N=BigInt(n),L=BigInt(limit);function c(v){return v>=2n?v*(v-1n)/2n:0n;}return Number(c(N+2n)-3n*c(N-L+1n)+3n*c(N-2n*L)-c(N-3n*L-1n));}
module.exports = solve;
