// Original candidate. Contract: https://leetcode.com/problems/longest-uploaded-prefix/
"use strict";
function solve(operations,args){const have=new Set(),out=[];let p=0;for(let i=0;i<operations.length;i++){let op=operations[i];if(op==='LUPrefix'){have.clear();p=0;out.push(null);}else if(op==='upload'){have.add(args[i][0]);while(have.has(p+1))p++;out.push(null);}else if(op==='longest')out.push(p);else throw Error('unknown operation');}return out;}
module.exports = solve;
