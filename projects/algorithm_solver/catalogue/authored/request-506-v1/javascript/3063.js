// Original candidate. Contract: https://leetcode.com/problems/linked-list-frequency/
"use strict";
function solve(head){const c=new Map();for(const x of head)c.set(x,(c.get(x)||0)+1);return [...c.values()];}
module.exports = solve;
