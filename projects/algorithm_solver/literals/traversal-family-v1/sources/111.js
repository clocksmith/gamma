function walk(a,b,f){let q=[[a,b]];while(q.length){let [n,s]=q.pop();if(n){s=f(n,s);q.push([n.right,s],[n.left,s]);}}}
function solve(a){if(!a)return 0;let r=Infinity;walk(a,0,(n,d)=>{if(!n.left&&!n.right)r=Math.min(r,d+1);return d+1;});return r;}
