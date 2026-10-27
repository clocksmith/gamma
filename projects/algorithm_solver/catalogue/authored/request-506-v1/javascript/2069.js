// Original candidate. Contract: https://leetcode.com/problems/walking-robot-simulation-ii/
"use strict";
function solve(operations,args){let w=0,h=0,p=0,moved=false;const out=[];for(let i=0;i<operations.length;i++){const op=operations[i],a=args[i];if(op==='Robot'){[w,h]=a;p=0;moved=false;out.push(null);}else if(op==='step'){p=(p+a[0])%(2*(w+h-2));moved=true;out.push(null);}else{let x,y,d;if(p===0){x=y=0;d=moved?'South':'East';}else if(p<=w-1){x=p;y=0;d='East';}else if(p<=w+h-2){x=w-1;y=p-w+1;d='North';}else if(p<=2*w+h-3){x=2*w+h-3-p;y=h-1;d='West';}else{x=0;y=2*(w+h-2)-p;d='South';}if(op==='getPos')out.push([x,y]);else if(op==='getDir')out.push(d);else throw Error('unknown operation');}}return out;}
module.exports = solve;
