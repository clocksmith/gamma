"use strict";
class SnapshotArray{constructor(length){this.history=Array.from({length},()=>[[0,0]]);this.current=0;}set(index,val){const h=this.history[index];if(h[h.length-1][0]===this.current)h[h.length-1]=[this.current,val];else h.push([this.current,val]);}snap(){return this.current++;}get(index,snap_id){const h=this.history[index];let l=0,r=h.length;while(l<r){const m=(l+r)>>1;if(h[m][0]<=snap_id)l=m+1;else r=m;}return h[l-1][1];}}

function solve(operations,args){const x=new SnapshotArray(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const v=x[operations[i]](...args[i]);out.push(v===undefined?null:v);}return out;}
module.exports=solve;
module.exports.SnapshotArray=SnapshotArray;
