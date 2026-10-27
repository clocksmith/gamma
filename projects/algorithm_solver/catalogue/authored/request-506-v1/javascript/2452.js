// Original candidate implementation. Contract: https://leetcode.com/problems/words-within-two-edits-of-dictionary/
"use strict";
function solve(queries,dictionary){return queries.filter(w=>dictionary.some(v=>{let d=0;for(let i=0;i<w.length;i++){if(w[i]!==v[i])d++;if(d>2)return false;}return true;}));}
module.exports = solve;
