// Original candidate implementation. Contract: https://leetcode.com/problems/design-an-atm-machine/
"use strict";
class ATM{constructor(){this.counts=Array(5).fill(0);}deposit(a){for(let i=0;i<5;i++)this.counts[i]+=a[i];}withdraw(amount){const values=[20,50,100,200,500],used=Array(5).fill(0);for(let i=4;i>=0;i--){used[i]=Math.min(this.counts[i],Math.floor(amount/values[i]));amount-=used[i]*values[i];}if(amount)return [-1];for(let i=0;i<5;i++)this.counts[i]-=used[i];return used;}}
function solve(operations,args){let obj;return operations.map((op,i)=>{if(op==='ATM'){obj=new ATM();return null;}return obj[op](...args[i])??null;});}
module.exports = solve;
