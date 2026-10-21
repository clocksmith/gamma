function solve(a){let r=0;for(let i=0;i<a.length;i++){if(i>r){return false;}r=Math.max(r,i+a[i]);}return true;}
