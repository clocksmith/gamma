function walk(a,b,f){let q=[[a,b]];while(q.length){let [n,s]=q.pop();if(n){s=f(n,s);q.push([n.right,s],[n.left,s]);}}}
function solve(a){let r=[];walk(a,0,(n,d)=>{(r[d]??=[]).push(n.val);return d+1;});for(let i=1;i<r.length;i+=2)r[i].reverse();return r;}
