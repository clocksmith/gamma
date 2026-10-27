// Original candidate implementation. Contract: https://leetcode.com/problems/design-memory-allocator/
"use strict";
class Allocator{constructor(n){this.memory=Array(n).fill(0);}allocate(size,id){let run=0;for(let i=0;i<this.memory.length;i++){run=this.memory[i]===0?run+1:0;if(run===size){const start=i-size+1;for(let j=start;j<=i;j++)this.memory[j]=id;return start;}}return -1;}freeMemory(id){let count=0;for(let i=0;i<this.memory.length;i++)if(this.memory[i]===id){this.memory[i]=0;count++;}return count;}}
function solve(operations,args){let obj;return operations.map((op,i)=>{if(op==='Allocator'){obj=new Allocator(...args[i]);return null;}return obj[op](...args[i]);});}
module.exports = solve;
