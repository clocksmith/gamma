// Original implementation. Contract: https://leetcode.com/problems/apply-operations-to-make-string-empty/
"use strict";
function solve(s){const count=new Map(),last=new Map();for(let i=0;i<s.length;i++){count.set(s[i],(count.get(s[i])||0)+1);last.set(s[i],i);}let mx=0;for(const x of count.values())mx=Math.max(mx,x);return [...s].filter((c,i)=>count.get(c)===mx&&last.get(c)===i).join('');}
module.exports = solve;
