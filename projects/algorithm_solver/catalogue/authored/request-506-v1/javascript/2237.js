// Original implementation. Contract: https://leetcode.com/problems/count-positions-on-street-with-required-brightness/
"use strict";
function solve(n,lights,requirement){const d=Array(n+1).fill(0);for(const [x,r] of lights){d[Math.max(0,x-r)]++;d[Math.min(n,x+r+1)]--;}let active=0,out=0;for(let i=0;i<n;i++){active+=d[i];out+=active>=requirement[i];}return out;}
module.exports = solve;
