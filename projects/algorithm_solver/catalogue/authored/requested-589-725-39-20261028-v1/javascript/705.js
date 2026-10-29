"use strict";
class MyHashSet{constructor(){this.present=new Uint8Array(1000001);}add(key){this.present[key]=1;}remove(key){this.present[key]=0;}contains(key){return this.present[key]===1;}}

function solve(operations,args){const instance=new MyHashSet(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const result=instance[operations[i]](...args[i]);out.push(result===undefined?null:result);}return out;}
module.exports=solve;
module.exports.MyHashSet=MyHashSet;
