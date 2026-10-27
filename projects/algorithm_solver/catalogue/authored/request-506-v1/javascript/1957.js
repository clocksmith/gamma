// Original implementation. Contract: https://leetcode.com/problems/delete-characters-to-make-fancy-string/
"use strict";
function solve(s){const out=[];for(const c of s)if(out.length<2||out.at(-1)!==c||out.at(-2)!==c)out.push(c);return out.join('');}
module.exports = solve;
