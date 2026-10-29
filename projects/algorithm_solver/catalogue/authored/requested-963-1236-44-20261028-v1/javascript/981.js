"use strict";
class TimeMap{constructor(){this.records=new Map();}set(key,value,timestamp){if(!this.records.has(key))this.records.set(key,{times:[],values:[]});const r=this.records.get(key);r.times.push(timestamp);r.values.push(value);}get(key,timestamp){const r=this.records.get(key);if(!r)return '';let l=0,h=r.times.length;while(l<h){const m=(l+h)>>1;if(r.times[m]<=timestamp)l=m+1;else h=m;}return l?r.values[l-1]:'';}}

function solve(operations,args){const x=new TimeMap(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const v=x[operations[i]](...args[i]);out.push(v===undefined?null:v);}return out;}
module.exports=solve;
module.exports.TimeMap=TimeMap;
