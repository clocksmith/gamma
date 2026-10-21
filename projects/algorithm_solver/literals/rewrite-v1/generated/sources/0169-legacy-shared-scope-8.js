function h(a){const b=new Map();for(const c of a){b.set(c,(b.get(c)||0)+1);}return b;}function solve(a){const b=h(a);for(const [c,d]of b){if(d>a.length/2)return c;}return 0;}
