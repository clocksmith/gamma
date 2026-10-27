// Original candidate. Contract: https://leetcode.com/problems/design-a-number-container-system/
"use strict";
function solve(operations,args){const current=new Map(),heaps=new Map(),out=[];function push(h,x){h.push(x);let i=h.length-1;while(i){let p=(i-1)>>1;if(h[p]<=x)break;h[i]=h[p];i=p;}h[i]=x;}function pop(h){const x=h.pop();if(!h.length)return;let i=0;while(i*2+1<h.length){let c=i*2+1;if(c+1<h.length&&h[c+1]<h[c])c++;if(h[c]>=x)break;h[i]=h[c];i=c;}h[i]=x;}
for(let i=0;i<operations.length;i++){const op=operations[i],a=args[i];if(op==='NumberContainers'){current.clear();heaps.clear();out.push(null);}else if(op==='change'){const [index,value]=a;current.set(index,value);if(!heaps.has(value))heaps.set(value,[]);push(heaps.get(value),index);out.push(null);}else if(op==='find'){const value=a[0],h=heaps.get(value)||[];while(h.length&&current.get(h[0])!==value)pop(h);out.push(h.length?h[0]:-1);}else throw Error('unknown operation');}return out;}
module.exports = solve;
