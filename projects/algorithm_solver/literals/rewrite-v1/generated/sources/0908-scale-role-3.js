function solve(a,b){let c=a[0];let d=a[0];for(const x of a){c=Math.min(c,x);d=Math.max(d,x);}return Math.max(0,d-c-b*2);}
