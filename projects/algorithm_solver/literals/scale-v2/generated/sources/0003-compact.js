function solve(a){const b=new Map();let c=0;let d=0;let e=0;for(const f of a){const g=b.get(f);if(g!==undefined&&g>=c){c=g+1;}b.set(f,d);e=Math.max(e,d-c+1);d++;}return e;}
