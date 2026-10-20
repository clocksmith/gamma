function solve(a){let b=0;for(let c=0;c<a.length;c++){if(c>b){return false;}b=Math.max(b,c+a[c]);}return true;}
