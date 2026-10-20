const solve=a=>{let r=1;let n=1;for(let i=1;i<a.length;i++){r=a[i-1]<a[i]?r+1:1;n=Math.max(n,r);}return n;};
