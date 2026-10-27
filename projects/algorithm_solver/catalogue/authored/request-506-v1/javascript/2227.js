/* Original candidate for LeetCode 2227. Contract: https://leetcode.com/problems/encrypt-and-decrypt-strings/
Development tests only; not admitted or independently qualified.
Batch adapter solve(operations, arguments) follows Encrypter class-call arrays.
Complexity: O(total dictionary characters + query characters) expected time; O(dictionary encoding size) space */
"use strict";
function solve(operations,args){let [keys,values,dictionary]=args[0],mapping=new Map(keys.map((k,i)=>[k,values[i]]));function encrypt(word){let out='';for(const c of word){if(!mapping.has(c))return '';out+=mapping.get(c);}return out;}let counts=new Map(),out=[null];for(const w of dictionary){let e=encrypt(w);if(e)counts.set(e,(counts.get(e)||0)+1);}for(let i=1;i<operations.length;i++)out.push(operations[i]==='encrypt'?encrypt(args[i][0]):counts.get(args[i][0])||0);return out;}
module.exports = solve;
