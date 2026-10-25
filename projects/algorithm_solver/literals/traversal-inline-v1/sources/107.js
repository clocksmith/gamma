function solve(a){let r=[];let q=[[a,0]];while(q.length){let [n,d]=q.pop();if(n){(r[d]??=[]).push(n.val);d++;q.push([n.right,d],[n.left,d]);}}return r.reverse();}
