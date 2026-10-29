"use strict";
class MyCircularQueue{constructor(k){this.data=new Array(k);this.head=0;this.size=0;}enQueue(value){if(this.isFull())return false;this.data[(this.head+this.size)%this.data.length]=value;this.size++;return true;}deQueue(){if(this.isEmpty())return false;this.head=(this.head+1)%this.data.length;this.size--;return true;}Front(){return this.isEmpty()?-1:this.data[this.head];}Rear(){return this.isEmpty()?-1:this.data[(this.head+this.size-1)%this.data.length];}isEmpty(){return this.size===0;}isFull(){return this.size===this.data.length;}}

function solve(operations,args){const instance=new MyCircularQueue(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const result=instance[operations[i]](...args[i]);out.push(result===undefined?null:result);}return out;}
module.exports=solve;
module.exports.MyCircularQueue=MyCircularQueue;
