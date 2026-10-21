function solve(a){let b=Infinity;let r=0;for(const x of a){b=Math.min(b,x);r=Math.max(r,x-b);}return r;}
