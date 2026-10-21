function h(a){const b=new Map();for(const c of a){b.set(c,(b.get(c)||0)+1);}return b;}const solve=a=>{const b=h(a);let c=0;for(const [a,d]of b){if(b.has(a+1))c=Math.max(c,d+b.get(a+1));}return c;};
