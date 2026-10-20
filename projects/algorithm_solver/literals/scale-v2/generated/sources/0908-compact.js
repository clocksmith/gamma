function solve(a,b){let c=a[0];let d=a[0];for(const e of a){c=Math.min(c,e);d=Math.max(d,e);}return Math.max(0,d-c-b*2);}
