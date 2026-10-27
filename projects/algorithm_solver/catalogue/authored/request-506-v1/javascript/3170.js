// Original implementation. Contract: https://leetcode.com/problems/lexicographically-minimum-string-after-removing-stars/
"use strict";
function solve(s){const stacks=Array.from({length:26},()=>[]),removed=new Set();for(let i=0;i<s.length;i++){if(s[i]==='*'){for(const stack of stacks)if(stack.length){removed.add(stack.pop());break;}}else stacks[s.charCodeAt(i)-97].push(i);}return [...s].filter((c,i)=>c!=='*'&&!removed.has(i)).join('');}
module.exports = solve;
