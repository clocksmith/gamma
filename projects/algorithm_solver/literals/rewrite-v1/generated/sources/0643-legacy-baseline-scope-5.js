function solve(a,b){let c=a.slice(0,b).reduce((a,b)=>a+b,0);let d=c;for(let e=b;e<a.length;e++){c+=a[e]-a[e-b];d=Math.max(d,c);}return d/b;}
