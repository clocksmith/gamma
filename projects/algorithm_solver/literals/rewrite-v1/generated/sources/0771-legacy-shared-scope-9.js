function h(a){const b=new Map();for(const c of a){b.set(c,(b.get(c)||0)+1);}return b;}function solve(a,b){const c=h(a);let d=0;for(const a of b){if(c.has(a))d++;}return d;}
