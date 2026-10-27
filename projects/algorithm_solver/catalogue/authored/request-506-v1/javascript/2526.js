// Original implementation. Contract: https://leetcode.com/problems/find-consecutive-integers-from-a-data-stream/
"use strict";
class DataStream{constructor(value,k){this.value=value;this.k=k;this.run=0;}consec(num){this.run=num===this.value?this.run+1:0;return this.run>=this.k;}}
function solve(ops,args){let obj;return ops.map((op,i)=>{if(op==='DataStream'){obj=new DataStream(...args[i]);return null;}return obj.consec(...args[i]);});}
module.exports = solve;
