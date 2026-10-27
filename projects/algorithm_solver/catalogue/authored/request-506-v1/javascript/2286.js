// Original candidate implementation. Contract: https://leetcode.com/problems/booking-concert-tickets-in-groups/
"use strict";
class BookMyShow{
 constructor(n,m){this.n=n;this.m=m;this.free=Array(n).fill(m);this.total=Array(4*n).fill(0);this.largest=Array(4*n).fill(0);const build=(p,l,r)=>{this.total[p]=(r-l+1)*m;this.largest[p]=m;if(l<r){const mid=(l+r)>>1;build(p*2,l,mid);build(p*2+1,mid+1,r);}};build(1,0,n-1);}
 update(index,value){this.free[index]=value;const put=(p,l,r)=>{if(l===r){this.total[p]=this.largest[p]=value;return;}const mid=(l+r)>>1;if(index<=mid)put(p*2,l,mid);else put(p*2+1,mid+1,r);this.total[p]=this.total[p*2]+this.total[p*2+1];this.largest[p]=Math.max(this.largest[p*2],this.largest[p*2+1]);};put(1,0,this.n-1);}
 first(k,limit){const find=(p,l,r)=>{if(l>limit||this.largest[p]<k)return -1;if(l===r)return l;const mid=(l+r)>>1,left=find(p*2,l,mid);return left>=0?left:find(p*2+1,mid+1,r);};return find(1,0,this.n-1);}
 prefix(limit){const sum=(p,l,r)=>{if(l>limit)return 0;if(r<=limit)return this.total[p];const mid=(l+r)>>1;return sum(p*2,l,mid)+sum(p*2+1,mid+1,r);};return sum(1,0,this.n-1);}
 gather(k,maxRow){const row=this.first(k,maxRow);if(row<0)return [];const seat=this.m-this.free[row];this.update(row,this.free[row]-k);return [row,seat];}
 scatter(k,maxRow){if(this.prefix(maxRow)<k)return false;while(k){const row=this.first(1,maxRow),take=Math.min(k,this.free[row]);this.update(row,this.free[row]-take);k-=take;}return true;}
}
function solve(operations,args){let obj;return operations.map((op,i)=>{if(op==='BookMyShow'){obj=new BookMyShow(...args[i]);return null;}return obj[op](...args[i]);});}
module.exports = solve;
