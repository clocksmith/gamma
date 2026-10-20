function solve(a){let b=a.reduce((a,b)=>a+b,0);let c=0;return a.findIndex(a=>{b-=a;const d=c===b;c+=a;return d;});}
