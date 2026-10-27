/* Original candidate for LeetCode 2353. Contract: https://leetcode.com/problems/design-a-food-rating-system/
Development tests only; not admitted or independently qualified.
Explicit stateful adapter: solve(operations, arguments), constructor first, void results null; exact official method semantics.
Complexity: O((n+q) log(n+q)) amortized time, O(n+q) space */
"use strict";
function solve(operations,args){const less=(a,b)=>a[0]!==b[0]?a[0]>b[0]:a[1]<b[1];function push(h,v){h.push(v);let i=h.length-1;while(i){let p=(i-1)>>1;if(!less(h[i],h[p]))break;[h[i],h[p]]=[h[p],h[i]];i=p;}}function pop(h){let v=h.pop();if(!h.length)return;h[0]=v;let i=0;while(2*i+1<h.length){let j=2*i+1;if(j+1<h.length&&less(h[j+1],h[j]))j++;if(!less(h[j],h[i]))break;[h[i],h[j]]=[h[j],h[i]];i=j;}}let[foods,cs,rs]=args[0],state=new Map(),heaps=new Map(),out=[null];for(let i=0;i<foods.length;i++){let f=foods[i],c=cs[i],r=rs[i];state.set(f,[c,r]);if(!heaps.has(c))heaps.set(c,[]);push(heaps.get(c),[r,f]);}for(let i=1;i<operations.length;i++){if(operations[i]==='changeRating'){let[f,r]=args[i],c=state.get(f)[0];state.set(f,[c,r]);push(heaps.get(c),[r,f]);out.push(null);}else{let h=heaps.get(args[i][0]);while(h[0][0]!==state.get(h[0][1])[1])pop(h);out.push(h[0][1]);}}return out;}
module.exports = solve;
