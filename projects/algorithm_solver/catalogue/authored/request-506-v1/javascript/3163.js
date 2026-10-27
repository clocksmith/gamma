// Original candidate implementation. Contract: https://leetcode.com/problems/string-compression-iii/
"use strict";
function solve(word){const out=[];for(let i=0;i<word.length;){let j=i+1;while(j<word.length&&j-i<9&&word[j]===word[i])j++;out.push(String(j-i)+word[i]);i=j;}return out.join('');}
module.exports = solve;
