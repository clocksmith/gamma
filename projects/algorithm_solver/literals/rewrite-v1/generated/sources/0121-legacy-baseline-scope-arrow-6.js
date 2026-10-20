const solve=a=>{let b=Infinity;let c=0;for(const d of a){b=Math.min(b,d);c=Math.max(c,d-b);}return c;};
