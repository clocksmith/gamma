var a=function(a){const r=[];for(;a;a=a.next){r.push(a.val);}const b=(a,c)=>{if(a>c){return null;}const d=a+c>>1;const e=b(a,d-1);const f=b(d+1,c);return new TreeNode(r[d],e,f);};return b(0,r.length-1);};function solve(b){return a(b);}
class TreeNode { constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; } }
