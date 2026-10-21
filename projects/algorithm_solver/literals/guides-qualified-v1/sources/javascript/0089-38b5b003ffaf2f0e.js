function solve(a){const b=2**a;const r=new Array(b);for(let i=0;i<b;i+=1){r[i]=i^i>>1;}return r;}
