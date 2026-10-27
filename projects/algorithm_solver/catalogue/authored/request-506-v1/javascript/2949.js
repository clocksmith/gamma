// Original implementation. Contract: https://leetcode.com/problems/count-beautiful-substrings-ii/
"use strict";
function solve(s,k){let base=1;while(base*base%k)base++;const period=2*base,counts=new Map([['0,0',1]]);let balance=0,answer=0;for(let i=1;i<=s.length;i++){balance+='aeiou'.includes(s[i-1])?1:-1;const key=(i%period)+','+balance;answer+=counts.get(key)||0;counts.set(key,(counts.get(key)||0)+1);}return answer;}
module.exports = solve;
