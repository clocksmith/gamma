const solve=a=>{let b=a[0],c=0;for(const d of a){c=Math.max(d,c+d);b=Math.max(b,c);}return b;};
