const solve=a=>{const b=new Map();for(const c of a)b.set(c,(b.get(c)||0)+1);let c=0;for(const [a,d]of b){if(b.has(a+1))c=Math.max(c,d+b.get(a+1));}return c;};
