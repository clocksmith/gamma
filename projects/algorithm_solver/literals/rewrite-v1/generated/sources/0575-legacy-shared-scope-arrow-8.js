function h(a){const b=new Map();for(const c of a){b.set(c,(b.get(c)||0)+1);}return b;}const solve=a=>{const b=h(a);return Math.min(b.size,Math.floor(a.length/2));};
