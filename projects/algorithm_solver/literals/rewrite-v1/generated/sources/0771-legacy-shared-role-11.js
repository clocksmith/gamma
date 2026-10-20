function h(a){const m=new Map();for(const x of a){m.set(x,(m.get(x)||0)+1);}return m;}function solve(a,b){const c=h(a);let r=0;for(const x of b){if(c.has(x))r++;}return r;}
