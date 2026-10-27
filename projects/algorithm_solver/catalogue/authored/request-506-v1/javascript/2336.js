// Original candidate. Contract: https://leetcode.com/problems/smallest-number-in-infinite-set/
"use strict";
function solve(operations,args){const absent=new Set(),out=[];for(let i=0;i<operations.length;i++){let op=operations[i];if(op==='SmallestInfiniteSet'){absent.clear();out.push(null);}else if(op==='addBack'){absent.delete(args[i][0]);out.push(null);}else if(op==='popSmallest'){let x=1;while(absent.has(x))x++;absent.add(x);out.push(x);}else throw Error('unknown operation');}return out;}
module.exports = solve;
