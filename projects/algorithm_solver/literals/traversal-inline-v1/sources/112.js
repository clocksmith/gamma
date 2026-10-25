function solve(a,b){let r=false;let q=[[a,b]];while(q.length){let [n,d]=q.pop();if(n){if(!n.left&&!n.right&&n.val===d)r=true;d-=n.val;q.push([n.right,d],[n.left,d]);}}return r;}
