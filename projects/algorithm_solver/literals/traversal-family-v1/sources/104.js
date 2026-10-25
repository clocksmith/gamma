function walk(a,b,f){let q=[[a,b]];while(q.length){let [n,s]=q.pop();if(n){s=f(n,s);q.push([n.right,s],[n.left,s]);}}}
function solve(a){let r=0;walk(a,0,(n,d)=>{r=Math.max(r,d+1);return d+1;});return r;}
