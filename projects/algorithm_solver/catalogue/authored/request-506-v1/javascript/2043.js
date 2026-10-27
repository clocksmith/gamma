// Original candidate. Contract: https://leetcode.com/problems/simple-bank-system/
"use strict";
function solve(operations,args){let b=[];const out=[];for(let i=0;i<operations.length;i++){let a=args[i],op=operations[i];if(op==='Bank'){b=a[0].map(BigInt);out.push(null);continue;}const valid=x=>x>=1&&x<=b.length;let ok;
 if(op==='deposit'){let[x,m]=a;m=BigInt(m);ok=valid(x);if(ok)b[x-1]+=m;}
 else if(op==='withdraw'){let[x,m]=a;m=BigInt(m);ok=valid(x)&&b[x-1]>=m;if(ok)b[x-1]-=m;}
 else if(op==='transfer'){let[x,y,m]=a;m=BigInt(m);ok=valid(x)&&valid(y)&&b[x-1]>=m;if(ok){b[x-1]-=m;b[y-1]+=m;}}
 else throw Error('unknown operation');out.push(ok);}return out;}
module.exports = solve;
