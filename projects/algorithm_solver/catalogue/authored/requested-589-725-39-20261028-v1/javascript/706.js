"use strict";
class MyHashMap{constructor(){this.values=new Int32Array(1000001);this.values.fill(-1);}put(key,value){this.values[key]=value;}get(key){return this.values[key];}remove(key){this.values[key]=-1;}}

function solve(operations,args){const instance=new MyHashMap(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const result=instance[operations[i]](...args[i]);out.push(result===undefined?null:result);}return out;}
module.exports=solve;
module.exports.MyHashMap=MyHashMap;
