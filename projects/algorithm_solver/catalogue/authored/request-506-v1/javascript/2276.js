/* Original candidate for LeetCode 2276. Contract: https://leetcode.com/problems/count-integers-in-intervals/
Development tests only; not admitted or independently qualified.
Batch adapter solve(operations, arguments) follows CountIntervals class-call arrays.
Complexity: O(q log U) amortized node creation, O(q log U) space, U=10^9; O(1) count */
"use strict";
function solve(operations,args){const tree=new Map(),out=[];function add(v,l,r,a,b){if((tree.get(v)||0)===r-l+1)return;if(a<=l&&r<=b){tree.set(v,r-l+1);return;}let m=Math.floor((l+r)/2);if(a<=m)add(v*2,l,m,a,b);if(b>m)add(v*2+1,m+1,r,a,b);tree.set(v,(tree.get(v*2)||0)+(tree.get(v*2+1)||0));}for(let i=0;i<operations.length;i++){let op=operations[i];if(op==='add'){add(1,1,1e9,...args[i]);out.push(null);}else if(op==='count')out.push(tree.get(1)||0);else out.push(null);}return out;}
module.exports = solve;
