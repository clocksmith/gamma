function solve(a){let r=0;let q=[[a,0]];while(q.length){let [n,d]=q.pop();if(n){d++;r=Math.max(r,d);q.push([n.right,d],[n.left,d]);}}return r;}
