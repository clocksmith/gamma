function h(a){const m=new Map();for(const x of a){m.set(x,(m.get(x)||0)+1);}return m;}function solve(a){const b=h(a);let r=0;for(const [x,y]of b){if(b.has(x+1))r=Math.max(r,y+b.get(x+1));}return r;}
