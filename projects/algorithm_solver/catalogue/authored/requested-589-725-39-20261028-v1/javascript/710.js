"use strict";
class Solution{constructor(n,blacklist){const blocked=new Set(blacklist);this.limit=n-blacklist.length;this.remap=new Map();let high=n-1;for(const value of blacklist)if(value<this.limit){while(blocked.has(high))high--;this.remap.set(value,high--);}}pick(){const ticket=Math.floor(Math.random()*this.limit);return this.remap.get(ticket)??ticket;}}

function solve(operations,args){const instance=new Solution(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const result=instance[operations[i]](...args[i]);out.push(result===undefined?null:result);}return out;}
module.exports=solve;
module.exports.Solution=Solution;
