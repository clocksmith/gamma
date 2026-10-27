// Original implementation. Contract: https://leetcode.com/problems/number-of-unique-categories/
"use strict";
function solve(n,categoryHandler){const same=Array.isArray(categoryHandler)?((a,b)=>categoryHandler[a]===categoryHandler[b]):((a,b)=>categoryHandler.haveSameCategory(a,b));const reps=[];for(let i=0;i<n;i++)if(!reps.some(j=>same(i,j)))reps.push(i);return reps.length;}
module.exports = solve;
