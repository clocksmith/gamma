function walk(a,b,f){let q=[[a,b]];while(q.length){let [n,s]=q.pop();if(n){s=f(n,s);q.push([n.right,s],[n.left,s]);}}}
function solve(a,b){let r=false;walk(a,b,(n,s)=>{if(!n.left&&!n.right&&n.val===s)r=true;return s-n.val;});return r;}
