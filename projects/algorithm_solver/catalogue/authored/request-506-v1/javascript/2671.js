// Original implementation. Contract: https://leetcode.com/problems/frequency-tracker/
"use strict";
class FrequencyTracker{constructor(){this.counts=new Map();this.freq=new Map();}change(x,d){const before=this.counts.get(x)||0;if(before)this.freq.set(before,(this.freq.get(before)||0)-1);const after=before+d;this.counts.set(x,after);if(after)this.freq.set(after,(this.freq.get(after)||0)+1);}add(x){this.change(x,1);return null;}deleteOne(x){if(this.counts.get(x))this.change(x,-1);return null;}hasFrequency(f){return (this.freq.get(f)||0)>0;}}
function solve(ops,args){let obj;return ops.map((op,i)=>{if(op==='FrequencyTracker'){obj=new FrequencyTracker();return null;}return obj[op](...args[i]);});}
module.exports = solve;
