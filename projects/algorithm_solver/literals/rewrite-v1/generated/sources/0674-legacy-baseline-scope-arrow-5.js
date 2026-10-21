const solve=a=>{let b=1;let c=1;for(let d=1;d<a.length;d++){b=a[d-1]<a[d]?b+1:1;c=Math.max(c,b);}return c;};
