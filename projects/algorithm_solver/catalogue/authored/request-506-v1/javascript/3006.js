// Original candidate implementation. Contract: https://leetcode.com/problems/find-beautiful-indices-in-the-given-array-i/
"use strict";
function solve(s,a,b,k){const aa=[],bb=[],out=[];for(let i=0;i<s.length;i++){if(s.startsWith(a,i))aa.push(i);if(s.startsWith(b,i))bb.push(i);}let j=0;for(const i of aa){while(j<bb.length&&bb[j]<i-k)j++;if(j<bb.length&&bb[j]<=i+k)out.push(i);}return out;}
module.exports = solve;
