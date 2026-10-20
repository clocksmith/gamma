function solve(a,b){let c=a.slice(0,b).reduce((a,b)=>a+b,0);let d=c;for(let i=b;i<a.length;i++){c+=a[i]-a[i-b];d=Math.max(d,c);}return d/b;}
