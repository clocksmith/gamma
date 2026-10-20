function solve(a){const m=new Map();for(const x of a)m.set(x,(m.get(x)||0)+1);let r=0;for(const [x,y]of m){if(m.has(x+1))r=Math.max(r,y+m.get(x+1));}return r;}
