function h(a){const m=new Map();for(const x of a){m.set(x,(m.get(x)||0)+1);}return m;}function solve(a){const b=h(a);return Math.min(b.size,Math.floor(a.length/2));}
