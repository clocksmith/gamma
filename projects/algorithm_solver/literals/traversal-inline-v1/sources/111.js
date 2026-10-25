function solve(a){if(!a)return 0;let r=Infinity;let q=[[a,0]];while(q.length){let [n,d]=q.pop();if(n){d++;if(!n.left&&!n.right)r=Math.min(r,d);q.push([n.right,d],[n.left,d]);}}return r;}
