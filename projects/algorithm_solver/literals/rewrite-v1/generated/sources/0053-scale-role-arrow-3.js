const solve=a=>{let b=a[0],r=0;for(const x of a){r=Math.max(x,r+x);b=Math.max(b,r);}return b;};
