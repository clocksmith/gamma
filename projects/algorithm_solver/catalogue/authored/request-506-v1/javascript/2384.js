// Original candidate implementation. Contract: https://leetcode.com/problems/largest-palindromic-number/
"use strict";
function solve(num){const counts=Array(10).fill(0);for(const c of num)counts[+c]++;let left='';for(let i=9;i>0;i--)left+=String(i).repeat(Math.floor(counts[i]/2));if(left)left+='0'.repeat(Math.floor(counts[0]/2));let middle='';for(let i=9;i>=0;i--)if(counts[i]%2){middle=String(i);break;}return left||middle?left+middle+[...left].reverse().join(''):'0';}
module.exports = solve;
