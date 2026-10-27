// Original candidate implementation. Contract: https://leetcode.com/problems/stock-price-fluctuation/
"use strict";
class MinHeap {
  constructor(){this.a=[];}
  push(v){const a=this.a;let i=a.length;a.push(v);while(i){const p=(i-1)>>1;if(a[p][0]<=v[0])break;a[i]=a[p];i=p;}a[i]=v;}
  pop(){const a=this.a,result=a[0],v=a.pop();if(a.length){let i=0;while(2*i+1<a.length){let j=2*i+1;if(j+1<a.length&&a[j+1][0]<a[j][0])j++;if(a[j][0]>=v[0])break;a[i]=a[j];i=j;}a[i]=v;}return result;}
}

class StockPrice{
 constructor(){this.prices=new Map();this.latest=0;this.low=new MinHeap();this.high=new MinHeap();}
 update(t,p){this.prices.set(t,p);this.latest=Math.max(this.latest,t);this.low.push([p,t]);this.high.push([-p,t]);}
 current(){return this.prices.get(this.latest);}
 minimum(){while(this.prices.get(this.low.a[0][1])!==this.low.a[0][0])this.low.pop();return this.low.a[0][0];}
 maximum(){while(this.prices.get(this.high.a[0][1])!==-this.high.a[0][0])this.high.pop();return -this.high.a[0][0];}
}
function solve(operations,args){let obj;return operations.map((op,i)=>{if(op==='StockPrice'){obj=new StockPrice();return null;}return obj[op](...args[i])??null;});}
module.exports = solve;
