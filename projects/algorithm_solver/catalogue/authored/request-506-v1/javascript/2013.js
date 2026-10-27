// Original candidate. Contract: https://leetcode.com/problems/detect-squares/
"use strict";
function solve(operations, args) {
 const pts=new Map(), out=[];const key=(x,y)=>x+","+y;
 for(let i=0;i<operations.length;i++){const op=operations[i],a=args[i];
 if(op==="DetectSquares"){pts.clear();out.push(null);}
 else if(op==="add"){const k=key(...a[0]);pts.set(k,(pts.get(k)||0)+1);out.push(null);}
 else if(op==="count"){const [x,y]=a[0];let sum=0;for(const [k,c]of pts){const [u,v]=k.split(',').map(Number);if(u!==x&&Math.abs(u-x)===Math.abs(v-y))sum+=c*(pts.get(key(u,y))||0)*(pts.get(key(x,v))||0);}out.push(sum);}
 else throw Error('unknown operation');}
 return out;
}
module.exports = solve;
