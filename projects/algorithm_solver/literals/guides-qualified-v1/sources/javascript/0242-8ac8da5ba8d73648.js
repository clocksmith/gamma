function solve(a,b){const m=new Map();for(const x of a){m.set(x,(m.get(x)||0)+1);}for(const x of b){m.set(x,(m.get(x)||0)-1);}return[...m.values()].every(a=>a===0);}
