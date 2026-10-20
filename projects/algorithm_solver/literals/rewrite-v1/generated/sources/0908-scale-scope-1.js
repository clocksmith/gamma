function solve(a,b){let c=a[0];let d=a[0];for(const b of a){c=Math.min(c,b);d=Math.max(d,b);}return Math.max(0,d-c-b*2);}
