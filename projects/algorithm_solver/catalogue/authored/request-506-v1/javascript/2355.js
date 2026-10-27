// Original implementation. Contract: https://leetcode.com/problems/maximum-number-of-books-you-can-take/
"use strict";
function solve(books){const stack=[],dp=Array(books.length).fill(0);let answer=0;for(let i=0;i<books.length;i++){const b=books[i];while(stack.length&&books[stack.at(-1)]-stack.at(-1)>=b-i)stack.pop();const j=stack.length?stack.at(-1):-1,len=Math.min(i-j,b);dp[i]=(2*b-len+1)*len/2+(j>=0?dp[j]:0);stack.push(i);answer=Math.max(answer,dp[i]);}return answer;}
module.exports = solve;
