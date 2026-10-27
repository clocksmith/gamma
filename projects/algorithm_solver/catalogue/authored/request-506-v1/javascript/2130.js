// Original candidate implementation. Contract: https://leetcode.com/problems/maximum-twin-sum-of-a-linked-list/
"use strict";
function solve(head){const a=[];for(let p=head;p;p=p.next)a.push(p.val);let best=0;for(let i=0;i<a.length/2;i++)best=Math.max(best,a[i]+a[a.length-1-i]);return best;}
module.exports = solve;
