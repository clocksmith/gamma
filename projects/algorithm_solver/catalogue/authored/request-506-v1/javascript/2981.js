// Original candidate implementation. Contract: https://leetcode.com/problems/find-longest-special-substring-that-occurs-thrice-i/
"use strict";
function solve(s){const counts=new Map();let answer=-1;for(let i=0;i<s.length;i++)for(let j=i;j<s.length&&s[j]===s[i];j++){const key=s[i]+(j-i+1),count=(counts.get(key)||0)+1;counts.set(key,count);if(count>=3)answer=Math.max(answer,j-i+1);}return answer;}
module.exports = solve;
