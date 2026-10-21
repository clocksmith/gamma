function h(a){let [r,b,c,d]=[-a[0],0,-a[0],0];for(let i=1;i<a.length;++i){r=Math.max(r,-a[i]);b=Math.max(b,r+a[i]);c=Math.max(c,b-a[i]);d=Math.max(d,c+a[i]);}return d;}function solve(a){return h(a);}
