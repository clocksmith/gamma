// Original candidate implementation. Contract: https://leetcode.com/problems/decremental-string-concatenation/
"use strict";
function solve(words){let dp=new Map([[words[0][0]+words[0].slice(-1),words[0].length]]);for(const word of words.slice(1)){const next=new Map();for(const [key,len] of dp){const a=key[0]+word.slice(-1),b=word[0]+key[1],x=len+word.length-Number(key[1]===word[0]),y=len+word.length-Number(word.slice(-1)===key[0]);next.set(a,Math.min(next.get(a)??Infinity,x));next.set(b,Math.min(next.get(b)??Infinity,y));}dp=next;}return Math.min(...dp.values());}
module.exports = solve;
